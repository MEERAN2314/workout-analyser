"""
Pydantic schemas for authentication
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    """User registration schema"""
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (8-72 bytes when UTF-8 encoded)")
    full_name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=13, le=120)
    height: Optional[float] = Field(None, ge=50, le=300, description="Height in cm")
    weight: Optional[float] = Field(None, ge=20, le=500, description="Weight in kg")
    fitness_level: Optional[str] = Field("beginner", pattern="^(beginner|intermediate|advanced)$")
    goals: Optional[List[str]] = Field(default_factory=list)
    
    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, v):
        """Validate password doesn't exceed 72 bytes (bcrypt limit)"""
        password_bytes = v.encode('utf-8')
        if len(password_bytes) > 72:
            # Auto-truncate at byte level
            truncated = password_bytes[:72].decode('utf-8', errors='ignore')
            return truncated
        return v
    
    @field_validator('goals')
    @classmethod
    def validate_goals(cls, v):
        valid_goals = [
            "weight_loss", "muscle_gain", "endurance", 
            "flexibility", "strength", "general_fitness"
        ]
        for goal in v:
            if goal not in valid_goals:
                raise ValueError(f"Invalid goal: {goal}. Must be one of {valid_goals}")
        return v

class UserLogin(BaseModel):
    """User login schema"""
    username: str = Field(..., description="Username or email")
    password: str

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")

class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[str] = None
    username: Optional[str] = None

class UserResponse(BaseModel):
    """User data response (without sensitive info)"""
    id: str = Field(..., alias="_id")
    username: str
    email: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    fitness_level: str
    goals: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "age": 25,
                "height": 175.5,
                "weight": 70.0,
                "fitness_level": "intermediate",
                "goals": ["weight_loss", "muscle_gain"],
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-15T10:00:00Z"
            }
        }

class UserUpdate(BaseModel):
    """User profile update schema"""
    full_name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=13, le=120)
    height: Optional[float] = Field(None, ge=50, le=300)
    weight: Optional[float] = Field(None, ge=20, le=500)
    fitness_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    goals: Optional[List[str]] = None
    
    @field_validator('goals')
    @classmethod
    def validate_goals(cls, v):
        if v is None:
            return v
        valid_goals = [
            "weight_loss", "muscle_gain", "endurance", 
            "flexibility", "strength", "general_fitness"
        ]
        for goal in v:
            if goal not in valid_goals:
                raise ValueError(f"Invalid goal: {goal}")
        return v

class PasswordChange(BaseModel):
    """Password change schema"""
    old_password: str
    new_password: str = Field(..., min_length=8, description="New password (8-72 bytes when UTF-8 encoded)")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_bytes(cls, v):
        """Validate password doesn't exceed 72 bytes (bcrypt limit)"""
        password_bytes = v.encode('utf-8')
        if len(password_bytes) > 72:
            # Auto-truncate at byte level
            truncated = password_bytes[:72].decode('utf-8', errors='ignore')
            return truncated
        return v

class RegisterResponse(BaseModel):
    """Registration response"""
    message: str
    user_id: str
    username: str
    email: str

class LoginResponse(BaseModel):
    """Login response with token and user data"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
