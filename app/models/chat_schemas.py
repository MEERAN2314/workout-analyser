"""
Pydantic schemas for AI chat functionality
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatSessionCreate(BaseModel):
    """Create new chat session"""
    workout_id: Optional[str] = Field(None, description="Optional workout ID for context")
    title: Optional[str] = Field(None, description="Optional custom title")

class ChatMessage(BaseModel):
    """Chat message schema"""
    content: str = Field(..., min_length=1, max_length=2000, description="Message content")

class ChatMessageResponse(BaseModel):
    """Chat message response"""
    id: str = Field(..., alias="_id")
    session_id: str
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    timestamp: datetime
    context_used: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True

class ChatSessionResponse(BaseModel):
    """Chat session response"""
    id: str = Field(..., alias="_id")
    user_id: str
    workout_id: Optional[str] = None
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True

class ChatHistoryResponse(BaseModel):
    """Chat history response"""
    session_id: str
    messages: List[ChatMessageResponse]
    total_messages: int

class AIResponse(BaseModel):
    """AI chat response"""
    response: str
    context_used: Optional[Dict[str, Any]] = None
    timestamp: str
    error: Optional[bool] = False

class ChatSessionsListResponse(BaseModel):
    """List of chat sessions"""
    sessions: List[ChatSessionResponse]
    total: int

class StartChatResponse(BaseModel):
    """Start chat response"""
    session_id: str
    message: str
    title: str