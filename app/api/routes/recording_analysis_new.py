"""
COMPLETE REWRITE - Recording Analysis with Proper Video Processing
"""
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import os
import uuid
from datetime import datetime
import cv2
import numpy as np

from app.core.database import get_database
from app.core.dependencies import get_current_user, get_current_user_optional
from app.services.google_drive_storage import google_drive_storage
from app.services.mediapipe_service import mediapipe_service
from app.models.workout import WorkoutSession, WorkoutCreate
from bson import ObjectId

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class VideoUploadResponse(BaseModel):
    session_id: str
    filename: str
    status: str
    message: str
    total_reps: int = 0
    accuracy: float = 0.0

class AnalysisResultsResponse(BaseModel):
    session_id: str
    exercise_name: str
    total_reps: int
    correct_reps: int
    accuracy_score: float
    form_feedback: List[str]
    mistakes: List[dict]
    calories_burned: Optional[float]
    video_url: Optional[str]
    analysis_timeline: List[dict]

@router.get("/", response_class=HTMLResponse)
async def recording_analysis_page(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Recording analysis page"""
    return templates.TemplateResponse(
        "recording_analysis_clean.html",
        {
            "request": request, 
            "title": "Recording Analysis",
            "user": current_user
        }
    )

@router.post("/upload-simple")
async def upload_and_process_video(
    file: UploadFile = File(...),
    exercise_name: str = "push_ups",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    SIMPLE UPLOAD AND PROCESS - No background tasks, direct processing
    Requires authentication
    """
    print("\n" + "="*80)
    print("🎬 VIDEO UPLOAD STARTED")
    print(f"   File: {file.filename}")
    print(f"   Exercise: {exercise_name}")
    print(f"   User: {current_user['username']}")
    print("="*80 + "\n")
    
    session_id = str(uuid.uuid4())
    
    try:
        # Step 1: Save video temporarily
        print("📥 Step 1: Saving video temporarily...")
        temp_path = f"/tmp/upload_{session_id}.mp4"
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_size = os.path.getsize(temp_path)
        print(f"✅ Video saved: {file_size / (1024*1024):.2f} MB")
        
        # Save to permanent location for later viewing
        permanent_path = f"/tmp/videos/workout_{session_id}.mp4"
        os.makedirs("/tmp/videos", exist_ok=True)
        
        import shutil
        shutil.copy(temp_path, permanent_path)
        print(f"✅ Video copied to permanent storage: {permanent_path}")
        
        # Step 2: Process video with MediaPipe
        print("\n🎯 Step 2: Processing video with MediaPipe...")
        result = await process_video_simple(temp_path, exercise_name, session_id)
        
        print(f"\n✅ Processing complete!")
        print(f"   Total Reps: {result['total_reps']}")
        print(f"   Accuracy: {result['accuracy']:.1f}%")
        print("="*80 + "\n")
        
        # Step 3: Save to database
        print("💾 Step 3: Saving to database...")
        db = get_database()
        if db is not None:
            workout_session = {
                "_id": ObjectId(session_id.replace('-', '')[:24]),
                "user_id": ObjectId(current_user["_id"]),
                "exercise_name": exercise_name,
                "session_type": "recording",
                "video_filename": file.filename,
                "video_path": permanent_path,  # Save video path
                "total_reps": result['total_reps'],
                "correct_reps": result['correct_reps'],
                "accuracy_score": result['accuracy'] / 100,
                "form_feedback": result['feedback'],
                "mistakes": result['mistakes'],
                "timeline_data": result['timeline'],
                "calories_burned": result['calories'],
                "duration": result['duration'],
                "analysis_completed": True,
                "created_at": datetime.utcnow()
            }
            
            await db.workouts.insert_one(workout_session)
            print(f"✅ Results saved to database for user {current_user['username']}")
        
        # Step 4: Generate annotated video
        print("\n🎨 Step 4: Generating annotated video...")
        annotated_path = None
        try:
            from app.services.video_annotator_simple import video_annotator_simple
            
            annotated_path = f"/tmp/videos/annotated_{session_id}.mp4"
            
            print(f"   Creating annotated video at: {annotated_path}")
            
            annotation_result = await video_annotator_simple.create_annotated_video(
                permanent_path,
                annotated_path,
                exercise_name,
                session_id + "_annotate"  # Use different session ID for annotation
            )
            
            # Verify file was created
            if os.path.exists(annotated_path) and os.path.getsize(annotated_path) > 0:
                print(f"✅ Annotated video generated: {os.path.getsize(annotated_path) / (1024*1024):.2f} MB")
                
                # Update database with annotated video path
                if db is not None:
                    await db.workouts.update_one(
                        {"_id": ObjectId(session_id.replace('-', '')[:24])},
                        {"$set": {"annotated_video_path": annotated_path}}
                    )
                    print("✅ Annotated video path saved to database")
            else:
                print("⚠️  Annotated video file not created or empty")
                annotated_path = None
            
        except Exception as anno_error:
            print(f"⚠️  Annotated video generation failed: {anno_error}")
            import traceback
            print(traceback.format_exc())
            annotated_path = None
            # Don't fail the whole upload if annotation fails
        
        # Cleanup
        try:
            os.remove(temp_path)
        except:
            pass
        
        return VideoUploadResponse(
            session_id=session_id,
            filename=file.filename,
            status="completed",
            message=f"Analysis complete! {result['total_reps']} reps detected",
            total_reps=result['total_reps'],
            accuracy=result['accuracy']
        )
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def process_video_simple(video_path: str, exercise_name: str, session_id: str) -> dict:
    """
    Simple video processing with MediaPipe
    """
    print(f"   Opening video: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Cannot open video file")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    print(f"   Video: {total_frames} frames, {fps} FPS, {duration:.1f}s")
    
    # Process frames
    frame_count = 0
    last_rep_count = 0
    correct_reps = 0
    accuracy_scores = []
    feedback_list = []
    mistakes = []
    timeline = []
    
    process_every = max(1, int(fps / 10))  # Process 10 frames per second
    
    print(f"   Processing every {process_every} frames...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Process every nth frame
        if frame_count % process_every == 0:
            timestamp = frame_count / fps
            
            try:
                # Analyze with MediaPipe
                analysis = mediapipe_service.process_frame(frame, exercise_name, session_id)
                
                if analysis:
                    # Update rep count
                    if analysis.rep_count > last_rep_count:
                        last_rep_count = analysis.rep_count
                        print(f"   🏋️  Rep {analysis.rep_count} at {timestamp:.1f}s")
                        
                        if analysis.accuracy_score > 0.7:
                            correct_reps += 1
                    
                    # Store data
                    if analysis.accuracy_score > 0:
                        accuracy_scores.append(analysis.accuracy_score)
                    
                    if analysis.form_feedback:
                        feedback_list.extend(analysis.form_feedback)
                    
                    # Timeline entry
                    timeline.append({
                        "timestamp": timestamp,
                        "rep_count": analysis.rep_count,
                        "phase": analysis.current_phase,
                        "accuracy_score": analysis.accuracy_score
                    })
                    
                    # Detect mistakes
                    if analysis.accuracy_score < 0.5 and analysis.form_feedback:
                        for feedback in analysis.form_feedback:
                            mistakes.append({
                                "timestamp": timestamp,
                                "description": feedback,
                                "severity": "medium"
                            })
            
            except Exception as e:
                print(f"   ⚠️  Frame {frame_count} error: {e}")
                continue
        
        # Progress
        if frame_count % (total_frames // 10) == 0:
            progress = (frame_count / total_frames) * 100
            print(f"   Progress: {progress:.0f}%")
    
    cap.release()
    mediapipe_service.reset_session(session_id)
    
    # Calculate results
    total_reps = last_rep_count
    avg_accuracy = (sum(accuracy_scores) / len(accuracy_scores) * 100) if accuracy_scores else 50.0
    calories = total_reps * 0.5  # Simple calculation
    
    print(f"\n   ✅ Analysis complete:")
    print(f"      Reps: {total_reps}")
    print(f"      Correct: {correct_reps}")
    print(f"      Accuracy: {avg_accuracy:.1f}%")
    
    return {
        "total_reps": total_reps,
        "correct_reps": correct_reps,
        "accuracy": avg_accuracy,
        "feedback": list(set(feedback_list))[:10],  # Unique, max 10
        "mistakes": mistakes[:10],  # Max 10
        "timeline": timeline,
        "calories": calories,
        "duration": duration
    }

@router.get("/results/{session_id}")
async def get_results(session_id: str):
    """Get analysis results"""
    try:
        db = get_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
        
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return AnalysisResultsResponse(
            session_id=session_id,
            exercise_name=session_doc.get("exercise_name", "unknown"),
            total_reps=session_doc.get("total_reps", 0),
            correct_reps=session_doc.get("correct_reps", 0),
            accuracy_score=session_doc.get("accuracy_score", 0.5),
            form_feedback=session_doc.get("form_feedback", []),
            mistakes=session_doc.get("mistakes", []),
            calories_burned=session_doc.get("calories_burned", 0),
            video_url=session_doc.get("video_url"),
            analysis_timeline=session_doc.get("timeline_data", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{session_id}")
async def download_pdf_report(session_id: str):
    """Generate and download PDF report"""
    try:
        print(f"\n📄 Generating PDF report for session {session_id}")
        
        # Get analysis results
        db = get_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
        
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Prepare data for report
        report_data = {
            "session_id": session_id,
            "exercise_name": session_doc.get("exercise_name", "unknown"),
            "total_reps": session_doc.get("total_reps", 0),
            "correct_reps": session_doc.get("correct_reps", 0),
            "accuracy_score": session_doc.get("accuracy_score", 0.5),
            "form_feedback": session_doc.get("form_feedback", []),
            "mistakes": session_doc.get("mistakes", []),
            "calories_burned": session_doc.get("calories_burned", 0),
            "duration": session_doc.get("duration", 0),
            "timeline_data": session_doc.get("timeline_data", []),
            "created_at": session_doc.get("created_at", datetime.utcnow())
        }
        
        # Generate PDF
        from app.services.report_generator import generate_workout_report
        pdf_buffer = await generate_workout_report(report_data)
        
        # Return as downloadable file
        filename = f"workout_report_{session_id[:8]}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        print(f"✅ PDF report generated: {filename}")
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.get("/video/{session_id}")
async def get_video_url(session_id: str):
    """Get original video URL"""
    try:
        print(f"\n🎥 Getting video URL for session {session_id}")
        
        db = get_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
        
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        video_path = session_doc.get("video_path")
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video file not found")
        
        print(f"✅ Video found: {video_path}")
        
        return JSONResponse({
            "session_id": session_id,
            "video_path": video_path,
            "exercise_name": session_doc.get("exercise_name", "unknown"),
            "duration": session_doc.get("duration", 0),
            "filename": session_doc.get("video_filename", "video.mp4")
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video-file/{session_id}")
async def stream_video(session_id: str):
    """Stream the original video file"""
    try:
        db = get_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
        
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        video_path = session_doc.get("video_path")
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Stream video file
        def iterfile():
            with open(video_path, mode="rb") as file_like:
                yield from file_like
        
        return StreamingResponse(
            iterfile(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"inline; filename={session_doc.get('video_filename', 'video.mp4')}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/annotated-video/{session_id}")
async def stream_annotated_video(session_id: str):
    """Stream the annotated video file with skeleton overlay"""
    try:
        print(f"\n🎥 Streaming annotated video for session: {session_id}")
        
        db = get_database()
        if db is None:
            print("❌ Database not available")
            raise HTTPException(status_code=503, detail="Database not available")
        
        session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
        
        if not session_doc:
            print(f"❌ Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        annotated_path = session_doc.get("annotated_video_path")
        
        print(f"   Annotated path from DB: {annotated_path}")
        
        if not annotated_path:
            print("❌ No annotated video path in database")
            raise HTTPException(status_code=404, detail="Annotated video not generated yet. Please wait for processing to complete.")
        
        if not os.path.exists(annotated_path):
            print(f"❌ Annotated video file not found at: {annotated_path}")
            raise HTTPException(status_code=404, detail=f"Annotated video file not found. It may have been deleted.")
        
        file_size = os.path.getsize(annotated_path)
        print(f"✅ Streaming annotated video: {file_size / (1024*1024):.2f} MB")
        
        # Stream annotated video file
        def iterfile():
            with open(annotated_path, mode="rb") as file_like:
                yield from file_like
        
        return StreamingResponse(
            iterfile(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"inline; filename=annotated_{session_doc.get('video_filename', 'video.mp4')}",
                "Accept-Ranges": "bytes"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error streaming annotated video: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{session_id}")
async def get_status(session_id: str):
    """Get processing status"""
    try:
        db = get_database()
        if db is None:
            return {"status": "unknown", "progress": 0}
        
        session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
        
        if not session_doc:
            return {"status": "not_found", "progress": 0}
        
        if session_doc.get("analysis_completed"):
            return {"status": "completed", "progress": 100, "results_available": True}
        else:
            return {"status": "processing", "progress": 50, "results_available": False}
            
    except Exception as e:
        return {"status": "error", "progress": 0, "message": str(e)}
