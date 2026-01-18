from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import json
import logging
import asyncio
import base64
import cv2
import numpy as np

from app.services.websocket_manager import connection_manager, create_session, get_session, end_session
from app.services.mediapipe_service import mediapipe_service
from app.core.database import get_database
from app.models.workout import WorkoutSession, WorkoutCreate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

class StartSessionRequest(BaseModel):
    exercise_name: str
    user_id: str  # In production, this would come from JWT token

class SessionResponse(BaseModel):
    session_id: str
    exercise_name: str
    status: str
    message: str

@router.get("/", response_class=HTMLResponse)
async def live_analysis_page(request: Request):
    """Live analysis page"""
    return templates.TemplateResponse(
        "live_analysis.html",
        {"request": request, "title": "Live Analysis"}
    )

@router.post("/start-session", response_model=SessionResponse)
async def start_live_session(request: StartSessionRequest):
    """Start live analysis session"""
    try:
        # Create new session
        session_id = create_session(request.user_id, request.exercise_name)
        
        # Store session in database
        db = get_database()
        if db is not None:
            workout_data = WorkoutCreate(
                exercise_name=request.exercise_name,
                session_type="live"
            )
            
            workout_session = WorkoutSession(
                user_id=request.user_id,
                **workout_data.dict()
            )
            
            await db.workouts.insert_one(workout_session.dict(by_alias=True))
            logger.info(f"Live session stored in database: {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            exercise_name=request.exercise_name,
            status="started",
            message="Live analysis session started successfully"
        )
        
    except Exception as e:
        logger.error(f"Error starting live session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start live session")

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for live analysis"""
    session = get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    try:
        # Connect to WebSocket
        await connection_manager.connect(
            websocket, 
            session_id, 
            session.user_id, 
            session.exercise_name
        )
        
        # Send initial connection confirmation
        await connection_manager.send_personal_message({
            'type': 'connected',
            'data': {
                'session_id': session_id,
                'exercise_name': session.exercise_name,
                'message': 'Connected successfully. Start your workout!'
            }
        }, session_id)
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_websocket_message(message, session_id, session)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                break
            except json.JSONDecodeError:
                await connection_manager.send_error(session_id, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                await connection_manager.send_error(session_id, "Processing error occurred")
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Clean up
        connection_manager.disconnect(session_id)
        mediapipe_service.reset_session(session_id)

async def handle_websocket_message(message: dict, session_id: str, session):
    """Handle incoming WebSocket messages"""
    message_type = message.get('type')
    
    if message_type == 'frame':
        await process_video_frame(message.get('data'), session_id, session)
    elif message_type == 'end_session':
        await handle_end_session(session_id, session)
    elif message_type == 'ping':
        await connection_manager.send_personal_message({
            'type': 'pong',
            'data': {'timestamp': message.get('data', {}).get('timestamp')}
        }, session_id)
    else:
        await connection_manager.send_error(session_id, f"Unknown message type: {message_type}")

async def process_video_frame(frame_data: dict, session_id: str, session):
    """Process video frame for exercise analysis"""
    try:
        # Decode base64 image
        image_data = frame_data.get('image')
        if not image_data:
            return
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64 to numpy array
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            await connection_manager.send_error(session_id, "Invalid image data")
            return
        
        # Process frame with MediaPipe
        result = mediapipe_service.process_frame(frame, session.exercise_name, session_id)
        
        if result:
            # Update session stats
            session.update_stats(result.rep_count, result.form_feedback, result.accuracy_score)
            
            # Send analysis result to client
            await connection_manager.send_analysis_result(session_id, {
                'rep_count': result.rep_count,
                'current_phase': result.current_phase,
                'form_feedback': result.form_feedback,
                'accuracy_score': result.accuracy_score
            })
            
            # Send specific feedback if available
            if result.form_feedback:
                await connection_manager.send_feedback(session_id, result.form_feedback)
        
    except Exception as e:
        logger.error(f"Error processing video frame: {e}")
        await connection_manager.send_error(session_id, "Frame processing error")

async def handle_end_session(session_id: str, session):
    """Handle session end request"""
    try:
        # Get final statistics
        final_stats = end_session(session_id)
        
        if final_stats:
            # Update database with final results
            db = get_database()
            if db is not None:
                await db.workouts.update_one(
                    {"user_id": session.user_id, "exercise_name": session.exercise_name},
                    {
                        "$set": {
                            "total_reps": final_stats['total_reps'],
                            "accuracy_score": final_stats['average_accuracy'],
                            "duration": final_stats['duration'],
                            "analysis_completed": True,
                            "form_feedback": final_stats['feedback_summary']
                        }
                    },
                    upsert=False
                )
            
            # Send final stats to client
            await connection_manager.send_session_complete(session_id, final_stats)
        
        # Clean up MediaPipe session
        mediapipe_service.reset_session(session_id)
        
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        await connection_manager.send_error(session_id, "Error ending session")

@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current session status"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    is_connected = connection_manager.is_session_active(session_id)
    mediapipe_stats = mediapipe_service.get_session_stats(session_id)
    
    return {
        "session_id": session_id,
        "exercise_name": session.exercise_name,
        "is_active": session.is_active,
        "is_connected": is_connected,
        "total_reps": mediapipe_stats.get('rep_count', 0),
        "current_phase": mediapipe_stats.get('current_phase', 'ready'),
        "duration": (session.start_time).total_seconds() if session.start_time else 0
    }

@router.post("/session/{session_id}/end")
async def end_session_endpoint(session_id: str):
    """End a live analysis session"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    final_stats = end_session(session_id)
    mediapipe_service.reset_session(session_id)
    
    if connection_manager.is_session_active(session_id):
        await connection_manager.send_session_complete(session_id, final_stats)
        connection_manager.disconnect(session_id)
    
    return {"message": "Session ended successfully", "final_stats": final_stats}