from fastapi import APIRouter, Request, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
import asyncio
import os
import uuid
from datetime import datetime
import mimetypes

from app.core.database import get_database
from app.services.google_drive_storage import google_drive_storage
from app.services.video_processor_fixed import video_processor_fixed as video_processor
from app.models.workout import WorkoutSession, WorkoutCreate
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

class VideoUploadResponse(BaseModel):
    session_id: str
    filename: str
    status: str
    message: str
    file_size: Optional[int] = None
    duration: Optional[float] = None
    processing_started: bool = False

class AnalysisStatusResponse(BaseModel):
    session_id: str
    status: str  # "uploaded", "processing", "completed", "failed"
    progress: int  # 0-100
    message: str
    estimated_completion: Optional[str] = None
    results_available: bool = False

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
    annotated_video_url: Optional[str]  # NEW: URL to annotated video with overlay
    analysis_timeline: List[dict]
    report_available: bool = False

@router.post("/debug-upload")
async def debug_upload(file: UploadFile = File(...)):
    """Debug endpoint to test file upload validation"""
    try:
        logger.info(f"Debug upload - File: {file.filename}, Size: {file.size}, Content-Type: {file.content_type}")
        
        # Test validation
        validation_result = await _validate_video_file(file)
        
        if not validation_result["valid"]:
            return {
                "status": "validation_failed",
                "error": validation_result["error"],
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size
            }
        
        # Test Google Drive service
        try:
            google_drive_storage.initialize()
            drive_status = "initialized" if google_drive_storage.initialized else "failed"
        except Exception as e:
            drive_status = f"error: {str(e)}"
        
        return {
            "status": "success",
            "validation": validation_result,
            "google_drive_status": drive_status,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size
        }
        
    except Exception as e:
        logger.error(f"Debug upload error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "filename": getattr(file, 'filename', 'unknown'),
            "content_type": getattr(file, 'content_type', 'unknown')
        }

@router.get("/direct", response_class=HTMLResponse)
async def direct_processing_page(request: Request):
    """Direct processing page (bypasses Celery)"""
    return templates.TemplateResponse(
        "direct_processing.html",
        {"request": request, "title": "Direct Processing"}
    )

@router.get("/", response_class=HTMLResponse)
async def recording_analysis_page(request: Request):
    """Enhanced recording analysis page with upload interface"""
    return templates.TemplateResponse(
        "recording_analysis_clean.html",
        {"request": request, "title": "Recording Analysis"}
    )

@router.post("/upload-direct", response_model=VideoUploadResponse)
async def upload_video_direct(
    file: UploadFile = File(...),
    exercise_name: str = "auto_detect",
    user_id: str = "demo_user"
):
    """
    Direct video upload and processing (bypasses Celery for immediate results)
    """
    try:
        # Validate file
        validation_result = await _validate_video_file(file)
        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create database entry
        db = get_database()
        if db is not None:
            from bson import ObjectId
            import hashlib
            
            if ObjectId.is_valid(user_id):
                user_object_id = ObjectId(user_id)
            else:
                hash_object = hashlib.md5(user_id.encode())
                user_object_id = ObjectId(hash_object.hexdigest()[:24])
            
            workout_data = WorkoutCreate(
                exercise_name=exercise_name,
                session_type="recording",
                video_filename=file.filename
            )
            
            workout_session = WorkoutSession(
                id=ObjectId(session_id.replace('-', '')[:24]),
                user_id=user_object_id,
                **workout_data.dict()
            )
            
            await db.workouts.insert_one(workout_session.dict(by_alias=True))
            logger.info(f"Direct processing session created: {session_id}")
        
        # Upload to Google Drive
        logger.info(f"Starting direct video upload: {file.filename}")
        await file.seek(0)
        
        video_url = google_drive_storage.upload_video(file.file, file.filename, user_id)
        
        if not video_url:
            raise HTTPException(status_code=500, detail="Failed to upload video to storage")
        
        # Update database with video URL
        if db is not None:
            await db.workouts.update_one(
                {"_id": ObjectId(session_id.replace('-', '')[:24])},
                {"$set": {"video_url": video_url, "processing_started": True}}
            )
        
        # Process video directly (no Celery)
        logger.info(f"🚀 Starting direct video processing for {session_id}")
        
        try:
            # Process the video directly
            result = await video_processor.process_video_from_url(video_url, exercise_name, session_id)
            
            # Save results to database
            if db is not None:
                update_data = result.to_dict()
                await db.workouts.update_one(
                    {"_id": ObjectId(session_id.replace('-', '')[:24])},
                    {"$set": update_data}
                )
            
            # Generate summary
            summary = await video_processor.generate_analysis_summary(result)
            
            logger.info(f"✅ Direct processing completed for {session_id}")
            
            return VideoUploadResponse(
                session_id=session_id,
                filename=file.filename,
                status="completed",
                message=f"Analysis completed! {result.total_reps} reps detected with {result.get_average_accuracy()*100:.1f}% accuracy",
                file_size=validation_result.get("file_size"),
                duration=result.duration,
                processing_started=True
            )
            
        except Exception as e:
            logger.error(f"❌ Direct processing failed: {e}")
            
            # Update database with error
            if db is not None:
                await db.workouts.update_one(
                    {"_id": ObjectId(session_id.replace('-', '')[:24])},
                    {"$set": {"status": "failed", "error_message": str(e)}}
                )
            
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in direct upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    exercise_name: str = "auto_detect",
    user_id: str = "demo_user"  # In production, get from JWT token
):
    """
    Smart video upload with Celery + Direct Processing fallback
    """
    logger.info("=" * 80)
    logger.info(f"🎬 UPLOAD ENDPOINT CALLED")
    logger.info(f"   File: {file.filename}")
    logger.info(f"   Exercise: {exercise_name}")
    logger.info(f"   User: {user_id}")
    logger.info("=" * 80)
    
    try:
        # Validate file
        logger.info("Step 1: Validating file...")
        validation_result = await _validate_video_file(file)
        if not validation_result["valid"]:
            logger.error(f"Validation failed: {validation_result['error']}")
            raise HTTPException(status_code=400, detail=validation_result["error"])
        logger.info(f"✅ File validated: {validation_result}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        logger.info(f"✅ Session ID generated: {session_id}")
        
        # Create database entry
        logger.info("Step 2: Creating database entry...")
        db = get_database()
        if db is not None:
            from bson import ObjectId
            import hashlib
            
            if ObjectId.is_valid(user_id):
                user_object_id = ObjectId(user_id)
            else:
                hash_object = hashlib.md5(user_id.encode())
                user_object_id = ObjectId(hash_object.hexdigest()[:24])
            
            workout_data = WorkoutCreate(
                exercise_name=exercise_name,
                session_type="recording",
                video_filename=file.filename
            )
            
            workout_session = WorkoutSession(
                id=ObjectId(session_id.replace('-', '')[:24]),
                user_id=user_object_id,
                **workout_data.dict()
            )
            
            await db.workouts.insert_one(workout_session.dict(by_alias=True))
            logger.info(f"✅ Database entry created for session {session_id}")
        
        # Upload to Google Drive
        logger.info(f"Step 3: Uploading to Google Drive...")
        await file.seek(0)
        
        video_url = google_drive_storage.upload_video(file.file, file.filename, user_id)
        
        if not video_url:
            logger.error("❌ Google Drive upload failed - no URL returned")
            raise HTTPException(status_code=500, detail="Failed to upload video to storage")
        
        logger.info(f"✅ Video uploaded to Google Drive: {video_url}")
        
        # Update database with video URL
        if db is not None:
            await db.workouts.update_one(
                {"_id": ObjectId(session_id.replace('-', '')[:24])},
                {"$set": {"video_url": video_url, "processing_started": False}}  # Set to False initially
            )
        
        logger.info(f"📹 Video uploaded to Google Drive: {video_url}")
        logger.info(f"🎯 Starting DIRECT processing (Celery disabled for debugging)")
        
        # FORCE DIRECT PROCESSING (bypass Celery for now)
        try:
            # Update database to indicate direct processing
            if db is not None:
                await db.workouts.update_one(
                    {"_id": ObjectId(session_id.replace('-', '')[:24])},
                    {"$set": {"processing_method": "direct", "processing_started": True}}
                )
            
            logger.info(f"🚀 Starting direct processing for {session_id}")
            logger.info(f"   Video URL: {video_url}")
            logger.info(f"   Exercise: {exercise_name}")
            logger.info(f"   User ID: {user_id}")
            
            # Process the video directly
            try:
                logger.info("📞 Calling video_processor.process_video_from_url...")
                result = await video_processor.process_video_from_url(
                    video_url, 
                    exercise_name, 
                    session_id,
                    generate_annotated=False
                )
                logger.info(f"✅ Video processing returned: {result.total_reps} reps, {result.get_average_accuracy():.2f} accuracy")
            except Exception as proc_error:
                logger.error(f"❌ Video processing failed: {proc_error}")
                import traceback
                logger.error(traceback.format_exc())
                raise
            
            # Save results to database
            if db is not None:
                update_data = result.to_dict()
                update_data["processing_method"] = "direct"
                logger.info(f"💾 Saving results to database...")
                await db.workouts.update_one(
                    {"_id": ObjectId(session_id.replace('-', '')[:24])},
                    {"$set": update_data}
                )
                logger.info(f"✅ Results saved to database")
            
            logger.info(f"🎉 Direct processing completed for {session_id}")
            
            return VideoUploadResponse(
                session_id=session_id,
                filename=file.filename,
                status="completed",
                message=f"Analysis completed! {result.total_reps} reps detected with {result.get_average_accuracy()*100:.1f}% accuracy",
                file_size=validation_result.get("file_size"),
                duration=result.duration,
                processing_started=True
            )
            
        except Exception as direct_error:
            logger.error(f"❌ Direct processing failed: {direct_error}")
            import traceback
            logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
            
            # Update database with error
            if db is not None:
                await db.workouts.update_one(
                    {"_id": ObjectId(session_id.replace('-', '')[:24])},
                    {"$set": {"status": "failed", "error_message": str(direct_error), "analysis_completed": False}}
                )
            
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(direct_error)}")
        
        # OLD CELERY CODE REMOVED FOR DEBUGGING
        # Will re-enable after direct processing works
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/debug-session/{session_id}")
async def debug_session_status(session_id: str):
    """Debug endpoint to check session and task status"""
    try:
        db = get_database()
        if db is None:
            return {"error": "Database not available"}
        
        # Find session in database
        from bson import ObjectId
        session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
        
        if not session_doc:
            return {"error": "Session not found", "session_id": session_id}
        
        # Get Celery task info
        celery_task_id = session_doc.get("celery_task_id")
        task_info = {}
        
        if celery_task_id:
            from app.services.celery_app import celery_app
            task_result = celery_app.AsyncResult(celery_task_id)
            
            task_info = {
                "task_id": celery_task_id,
                "state": task_result.state,
                "info": task_result.info,
                "ready": task_result.ready(),
                "successful": task_result.successful() if task_result.ready() else None,
                "failed": task_result.failed() if task_result.ready() else None
            }
        
        return {
            "session_id": session_id,
            "session_data": {
                "exercise_name": session_doc.get("exercise_name"),
                "video_url": session_doc.get("video_url"),
                "analysis_completed": session_doc.get("analysis_completed", False),
                "processing_started": session_doc.get("processing_started", False),
                "celery_task_id": celery_task_id
            },
            "task_info": task_info
        }
        
    except Exception as e:
        return {"error": str(e), "session_id": session_id}

@router.get("/status/{session_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(session_id: str):
    """Get current analysis status for a recording session"""
    try:
        db = get_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Find session in database
        from bson import ObjectId
        session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
        
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if analysis is completed
        analysis_completed = session_doc.get("analysis_completed", False)
        
        if analysis_completed:
            return AnalysisStatusResponse(
                session_id=session_id,
                status="completed",
                progress=100,
                message="Analysis completed successfully",
                results_available=True
            )
        
        # Check processing method and status
        processing_method = session_doc.get("processing_method", "celery")
        
        if processing_method == "direct":
            # Direct processing - check completion status
            if analysis_completed:
                return AnalysisStatusResponse(
                    session_id=session_id,
                    status="completed",
                    progress=100,
                    message="Analysis completed successfully",
                    results_available=True
                )
            else:
                return AnalysisStatusResponse(
                    session_id=session_id,
                    status="processing",
                    progress=50,
                    message="Direct processing in progress...",
                    results_available=False
                )
        
        # Celery processing - check task status
        celery_task_id = session_doc.get("celery_task_id")
        if celery_task_id:
            from app.services.celery_app import celery_app
            
            # Get task result directly from Celery
            task_result = celery_app.AsyncResult(celery_task_id)
            
            if task_result.state == 'SUCCESS':
                status = "completed"
                progress = 100
                message = "Analysis completed successfully"
                results_available = True
            elif task_result.state == 'FAILURE':
                status = "failed"
                progress = 0
                error_info = task_result.info if task_result.info else "Unknown error"
                if isinstance(error_info, dict):
                    message = f"Analysis failed: {error_info.get('error', 'Unknown error')}"
                else:
                    message = f"Analysis failed: {str(error_info)}"
                results_available = False
            elif task_result.state == 'PROGRESS':
                status = "processing"
                progress = task_result.info.get('progress', 50) if task_result.info else 50
                message = task_result.info.get('status', 'Processing video...') if task_result.info else 'Processing video...'
                results_available = False
            else:  # PENDING
                status = "processing"
                progress = 10
                message = "Analysis queued, waiting to start..."
                results_available = False
        else:
            # Fallback to basic status checking
            video_url = session_doc.get("video_url")
            if video_url:
                status = "processing"
                progress = 25
                message = "Video uploaded, analysis in progress..."
                results_available = False
            else:
                status = "uploaded"
                progress = 5
                message = "Video uploaded, preparing for analysis..."
                results_available = False
        
        return AnalysisStatusResponse(
            session_id=session_id,
            status=status,
            progress=progress,
            message=message,
            results_available=results_available
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")

@router.get("/results/{session_id}", response_model=AnalysisResultsResponse)
async def get_analysis_results(session_id: str):
    """Get comprehensive analysis results for a completed session"""
    try:
        db = get_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Find session in database
        from bson import ObjectId
        session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
        
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not session_doc.get("analysis_completed", False):
            raise HTTPException(status_code=202, detail="Analysis not yet completed")
        
        # Extract results
        return AnalysisResultsResponse(
            session_id=session_id,
            exercise_name=session_doc.get("exercise_name", "unknown"),
            total_reps=session_doc.get("total_reps", 0),
            correct_reps=session_doc.get("correct_reps", 0),
            accuracy_score=session_doc.get("accuracy_score", 0.0),
            form_feedback=session_doc.get("form_feedback", []),
            mistakes=session_doc.get("mistakes", []),
            calories_burned=session_doc.get("calories_burned"),
            video_url=session_doc.get("video_url"),
            annotated_video_url=session_doc.get("annotated_video_url"),  # NEW: Include annotated video
            analysis_timeline=session_doc.get("analysis_timeline", []),
            report_available=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get results")

@router.get("/report/{session_id}")
async def download_report(session_id: str):
    """Generate and download PDF report for analysis results"""
    try:
        # Get analysis results
        results = await get_analysis_results(session_id)
        
        # Convert to dict for report generation
        results_dict = {
            "session_id": results.session_id,
            "exercise_name": results.exercise_name,
            "total_reps": results.total_reps,
            "correct_reps": results.correct_reps,
            "accuracy_score": results.accuracy_score,
            "form_feedback": results.form_feedback,
            "mistakes": results.mistakes,
            "calories_burned": results.calories_burned,
            "analysis_timeline": results.analysis_timeline,
            "duration": 0,  # Will be fetched from DB if needed
            "processed_frames": 0  # Will be fetched from DB if needed
        }
        
        # Get additional data from database
        db = get_database()
        if db is not None:
            from bson import ObjectId
            session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
            if session_doc:
                results_dict["duration"] = session_doc.get("duration", 0)
                results_dict["processed_frames"] = session_doc.get("processed_frames", 0)
        
        # Generate PDF report
        from app.services.report_generator import generate_workout_report
        pdf_buffer = await generate_workout_report(results_dict)
        
        # Return PDF as downloadable file
        from fastapi.responses import StreamingResponse
        
        filename = f"workout_report_{session_id[:8]}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
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
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.get("/video/{session_id}")
async def get_video_url(session_id: str):
    """Get video URL for playback"""
    try:
        db = get_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Find session in database
        from bson import ObjectId
        session_doc = await db.workouts.find_one({"_id": ObjectId(session_id.replace('-', '')[:24])})
        
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        video_url = session_doc.get("video_url")
        
        if not video_url:
            raise HTTPException(status_code=404, detail="Video not found for this session")
        
        return JSONResponse({
            "session_id": session_id,
            "video_url": video_url,
            "exercise_name": session_doc.get("exercise_name", "unknown"),
            "duration": session_doc.get("duration", 0)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video URL")

async def _validate_video_file(file: UploadFile) -> dict:
    """Validate uploaded video file with improved error handling"""
    try:
        logger.info(f"Validating file: {file.filename}, content_type: {file.content_type}")
        
        # Check file extension
        if not file.filename:
            return {"valid": False, "error": "No filename provided"}
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = [f".{ext}" for ext in settings.ALLOWED_VIDEO_EXTENSIONS.split(",")]
        
        logger.info(f"File extension: {file_ext}, allowed: {allowed_extensions}")
        
        if file_ext not in allowed_extensions:
            return {
                "valid": False, 
                "error": f"Unsupported file format '{file_ext}'. Allowed: {', '.join(allowed_extensions)}"
            }
        
        # Check file size - improved method
        file_size = 0
        try:
            # Try to get size from file.size first (if available)
            if hasattr(file, 'size') and file.size is not None:
                file_size = file.size
                logger.info(f"Got file size from file.size: {file_size}")
            else:
                # Fallback: read the content to get size
                content = await file.read()
                file_size = len(content)
                logger.info(f"Got file size from content length: {file_size}")
                
                # Reset file pointer by creating a new file-like object
                from io import BytesIO
                file.file = BytesIO(content)
                await file.seek(0)
                
        except Exception as e:
            logger.error(f"Error checking file size: {e}")
            # If we can't determine size, be lenient and continue
            file_size = 0
            logger.warning("Could not determine file size, skipping size check")
        
        # Only check size if we successfully got it
        if file_size > 0:
            max_size_bytes = settings.MAX_FILE_SIZE * 1024 * 1024  # Convert MB to bytes
            if file_size > max_size_bytes:
                return {
                    "valid": False,
                    "error": f"File too large ({file_size / (1024*1024):.1f}MB). Maximum size: {settings.MAX_FILE_SIZE}MB"
                }
        
        # More flexible MIME type checking
        mime_type = None
        
        # First try the uploaded content type
        if file.content_type and file.content_type.startswith('video/'):
            mime_type = file.content_type
            logger.info(f"Using uploaded content type: {mime_type}")
        else:
            # Fallback to guessing from filename
            mime_type, _ = mimetypes.guess_type(file.filename)
            logger.info(f"Guessed MIME type: {mime_type}")
        
        # Accept common video MIME types and extensions
        valid_video_types = [
            'video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 
            'video/x-msvideo', 'video/x-matroska', 'video/webm'
        ]
        
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        
        # Check if either MIME type is valid OR extension is valid
        mime_valid = mime_type and any(mime_type.startswith(vt.split('/')[0]) for vt in valid_video_types)
        ext_valid = file_ext in valid_extensions
        
        if not (mime_valid or ext_valid):
            logger.warning(f"MIME type validation failed: {mime_type}, extension: {file_ext}")
            # Be more lenient - if extension is in our allowed list, accept it
            if file_ext in allowed_extensions:
                logger.info("Accepting file based on extension despite MIME type issue")
                mime_type = f"video/{file_ext[1:]}"  # Create a MIME type from extension
            else:
                return {
                    "valid": False, 
                    "error": f"File does not appear to be a valid video. MIME type: {mime_type}, Extension: {file_ext}"
                }
        
        logger.info(f"File validation passed: {file.filename}")
        
        return {
            "valid": True,
            "file_size": file_size,
            "mime_type": mime_type or f"video/{file_ext[1:]}",
            "duration": None  # Will be extracted during processing
        }
        
    except Exception as e:
        logger.error(f"Error validating file: {e}")
        return {"valid": False, "error": f"File validation failed: {str(e)}"}

