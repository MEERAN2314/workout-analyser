"""
AI Chat API Routes - LangChain + Gemini 2.0 Flash integration
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Dict, Any, Optional
import logging

from app.core.dependencies import get_current_user
from app.services.ai_chat_service import ai_chat_service
from app.models.chat_schemas import (
    ChatSessionCreate, ChatMessage, ChatMessageResponse, 
    ChatSessionResponse, ChatHistoryResponse, AIResponse,
    ChatSessionsListResponse, StartChatResponse
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

# ============================================================================
# HTML Pages
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    """AI Chat page - authentication handled client-side"""
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "title": "AI Workout Coach"
        }
    )

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/api/start", response_model=StartChatResponse)
async def start_chat_session(
    session_data: ChatSessionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Start a new AI chat session
    
    - **workout_id**: Optional workout ID for context-specific consultation
    - **title**: Optional custom title for the session
    """
    try:
        session_id = await ai_chat_service.start_chat_session(
            user_id=current_user["_id"],
            workout_id=session_data.workout_id
        )
        
        # Get the welcome message
        history = await ai_chat_service.get_chat_history(session_id, limit=1)
        welcome_message = history[0]["content"] if history else "Hello! How can I help you with your workout today?"
        
        title = session_data.title or "Workout Consultation"
        
        logger.info(f"Started chat session {session_id} for user {current_user['username']}")
        
        return StartChatResponse(
            session_id=session_id,
            message=welcome_message,
            title=title
        )
        
    except Exception as e:
        logger.error(f"Error starting chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start chat session"
        )

@router.post("/api/{session_id}/message", response_model=AIResponse)
async def send_message(
    session_id: str,
    message: ChatMessage,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send a message to the AI coach
    
    - **session_id**: Chat session ID
    - **content**: Message content (1-2000 characters)
    
    Returns AI response with context information
    """
    try:
        # Verify session belongs to user (this will be checked in the service)
        response = await ai_chat_service.send_message(
            session_id=session_id,
            user_message=message.content
        )
        
        logger.info(f"AI response sent for session {session_id}")
        
        return AIResponse(**response)
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )

@router.get("/api/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get chat history for a session
    
    - **session_id**: Chat session ID
    - **limit**: Maximum number of messages to return (default: 50, max: 100)
    """
    try:
        # Limit validation
        limit = min(limit, 100)
        
        messages = await ai_chat_service.get_chat_history(session_id, limit)
        
        # Convert to response models
        message_responses = []
        for msg in messages:
            message_responses.append(ChatMessageResponse(**msg))
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=message_responses,
            total_messages=len(message_responses)
        )
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat history"
        )

@router.get("/api/sessions", response_model=ChatSessionsListResponse)
async def get_chat_sessions(
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user's chat sessions
    
    - **limit**: Maximum number of sessions to return (default: 20, max: 50)
    """
    try:
        # Limit validation
        limit = min(limit, 50)
        
        sessions = await ai_chat_service.get_user_chat_sessions(
            user_id=current_user["_id"],
            limit=limit
        )
        
        # Convert to response models
        session_responses = []
        for session in sessions:
            session_responses.append(ChatSessionResponse(**session))
        
        return ChatSessionsListResponse(
            sessions=session_responses,
            total=len(session_responses)
        )
        
    except Exception as e:
        logger.error(f"Error getting chat sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat sessions"
        )

@router.delete("/api/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a chat session and all its messages
    
    - **session_id**: Chat session ID to delete
    
    Warning: This action cannot be undone
    """
    try:
        success = await ai_chat_service.delete_chat_session(
            session_id=session_id,
            user_id=current_user["_id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found or access denied"
            )
        
        logger.info(f"Deleted chat session {session_id} for user {current_user['username']}")
        
        return {"message": "Chat session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session"
        )

@router.get("/api/{session_id}/info")
async def get_session_info(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get basic information about a chat session
    
    - **session_id**: Chat session ID
    """
    try:
        from app.core.database import get_database
        from bson import ObjectId
        
        db = get_database()
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        session = await db.chat_sessions.find_one({
            "_id": ObjectId(session_id),
            "user_id": ObjectId(current_user["_id"])
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Convert ObjectId to string
        session["_id"] = str(session["_id"])
        session["user_id"] = str(session["user_id"])
        if session.get("workout_id"):
            session["workout_id"] = str(session["workout_id"])
        
        return ChatSessionResponse(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session info"
        )

# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/api/quick-start")
async def quick_start_chat(
    workout_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Quick start a chat session (convenience endpoint)
    
    - **workout_id**: Optional workout ID for context
    """
    try:
        session_data = ChatSessionCreate(workout_id=workout_id)
        return await start_chat_session(session_data, current_user)
        
    except Exception as e:
        logger.error(f"Error in quick start: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start chat"
        )

@router.post("/api/{session_id}/quick-message")
async def send_quick_message(
    session_id: str,
    content: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send a quick message (convenience endpoint)
    
    - **session_id**: Chat session ID
    - **content**: Message content as query parameter
    """
    try:
        message = ChatMessage(content=content)
        return await send_message(session_id, message, current_user)
        
    except Exception as e:
        logger.error(f"Error sending quick message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )