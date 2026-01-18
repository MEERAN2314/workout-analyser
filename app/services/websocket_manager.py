from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
import logging
import asyncio
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections by session_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store session metadata
        self.session_metadata: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str, exercise_name: str):
        """Accept WebSocket connection and store session info"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_metadata[session_id] = {
            'user_id': user_id,
            'exercise_name': exercise_name,
            'connected_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove connection and session data"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_personal_message(self, message: dict, session_id: str):
        """Send message to specific session"""
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_text(json.dumps(message))
                
                # Update last activity
                if session_id in self.session_metadata:
                    self.session_metadata[session_id]['last_activity'] = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                # Remove broken connection
                self.disconnect(session_id)
    
    async def send_analysis_result(self, session_id: str, analysis_result: dict):
        """Send exercise analysis result to client"""
        message = {
            'type': 'analysis_result',
            'data': analysis_result,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.send_personal_message(message, session_id)
    
    async def send_feedback(self, session_id: str, feedback: List[str]):
        """Send form feedback to client"""
        message = {
            'type': 'feedback',
            'data': {
                'feedback': feedback
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.send_personal_message(message, session_id)
    
    async def send_rep_count(self, session_id: str, rep_count: int, current_phase: str):
        """Send rep count update to client"""
        message = {
            'type': 'rep_update',
            'data': {
                'rep_count': rep_count,
                'current_phase': current_phase
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.send_personal_message(message, session_id)
    
    async def send_error(self, session_id: str, error_message: str):
        """Send error message to client"""
        message = {
            'type': 'error',
            'data': {
                'message': error_message
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.send_personal_message(message, session_id)
    
    async def send_session_complete(self, session_id: str, final_stats: dict):
        """Send session completion message with final statistics"""
        message = {
            'type': 'session_complete',
            'data': final_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.send_personal_message(message, session_id)
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.active_connections.keys())
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session metadata"""
        return self.session_metadata.get(session_id)
    
    def is_session_active(self, session_id: str) -> bool:
        """Check if session is active"""
        return session_id in self.active_connections
    
    async def cleanup_inactive_sessions(self, timeout_minutes: int = 30):
        """Clean up sessions that have been inactive for too long"""
        current_time = datetime.utcnow()
        inactive_sessions = []
        
        for session_id, metadata in self.session_metadata.items():
            last_activity = metadata.get('last_activity', current_time)
            if (current_time - last_activity).total_seconds() > (timeout_minutes * 60):
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            logger.info(f"Cleaning up inactive session: {session_id}")
            self.disconnect(session_id)

# Global connection manager instance
connection_manager = ConnectionManager()

class LiveAnalysisSession:
    """Manages individual live analysis sessions"""
    
    def __init__(self, session_id: str, user_id: str, exercise_name: str):
        self.session_id = session_id
        self.user_id = user_id
        self.exercise_name = exercise_name
        self.start_time = datetime.utcnow()
        self.total_reps = 0
        self.feedback_history = []
        self.accuracy_scores = []
        self.is_active = True
    
    def update_stats(self, rep_count: int, feedback: List[str], accuracy_score: float):
        """Update session statistics"""
        self.total_reps = rep_count
        if feedback:
            self.feedback_history.extend(feedback)
        if accuracy_score > 0:
            self.accuracy_scores.append(accuracy_score)
    
    def get_final_stats(self) -> Dict:
        """Get final session statistics"""
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        avg_accuracy = sum(self.accuracy_scores) / len(self.accuracy_scores) if self.accuracy_scores else 0.0
        
        return {
            'session_id': self.session_id,
            'exercise_name': self.exercise_name,
            'total_reps': self.total_reps,
            'duration': duration,
            'average_accuracy': avg_accuracy,
            'feedback_summary': list(set(self.feedback_history)),  # Unique feedback items
            'completed_at': datetime.utcnow().isoformat()
        }
    
    def end_session(self):
        """Mark session as ended"""
        self.is_active = False

# Session storage
active_sessions: Dict[str, LiveAnalysisSession] = {}

def create_session(user_id: str, exercise_name: str) -> str:
    """Create a new live analysis session"""
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = LiveAnalysisSession(session_id, user_id, exercise_name)
    return session_id

def get_session(session_id: str) -> Optional[LiveAnalysisSession]:
    """Get session by ID"""
    return active_sessions.get(session_id)

def end_session(session_id: str) -> Optional[Dict]:
    """End session and return final stats"""
    if session_id in active_sessions:
        session = active_sessions[session_id]
        final_stats = session.get_final_stats()
        session.end_session()
        del active_sessions[session_id]
        return final_stats
    return None