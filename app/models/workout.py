from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class ExerciseResult(BaseModel):
    exercise_name: str
    total_reps: int
    correct_reps: int
    accuracy_score: float = Field(..., ge=0, le=1)
    form_feedback: List[str] = []
    mistakes: List[Dict[str, Any]] = []
    calories_burned: Optional[float] = None

class WorkoutSession(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    session_type: str = Field(..., regex="^(live|recording)$")
    
    # Exercise details
    exercise_name: str
    duration: Optional[float] = None  # in seconds
    
    # Analysis results
    total_reps: int = 0
    correct_reps: int = 0
    accuracy_score: float = Field(default=0.0, ge=0, le=1)
    form_feedback: List[str] = []
    mistakes: List[Dict[str, Any]] = []
    
    # Video details (for recording analysis)
    video_url: Optional[str] = None  # GCS URL
    video_filename: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    # Performance metrics
    calories_burned: Optional[float] = None
    average_form_score: Optional[float] = None
    improvement_suggestions: List[str] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_completed: bool = False
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class WorkoutCreate(BaseModel):
    exercise_name: str
    session_type: str = Field(..., regex="^(live|recording)$")
    video_filename: Optional[str] = None

class WorkoutUpdate(BaseModel):
    total_reps: Optional[int] = None
    correct_reps: Optional[int] = None
    accuracy_score: Optional[float] = Field(None, ge=0, le=1)
    form_feedback: Optional[List[str]] = None
    mistakes: Optional[List[Dict[str, Any]]] = None
    calories_burned: Optional[float] = None
    average_form_score: Optional[float] = None
    improvement_suggestions: Optional[List[str]] = None
    analysis_completed: Optional[bool] = None
    duration: Optional[float] = None

class Exercise(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    category: str  # e.g., "upper_body", "lower_body", "cardio"
    description: str
    instructions: List[str]
    target_muscles: List[str]
    difficulty_level: str = Field(..., regex="^(beginner|intermediate|advanced)$")
    equipment_needed: List[str] = []
    
    # MediaPipe specific configurations
    key_landmarks: List[str] = []  # Important pose landmarks for this exercise
    form_rules: Dict[str, Any] = {}  # Exercise-specific form validation rules
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}