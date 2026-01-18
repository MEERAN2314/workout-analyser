from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    MONGODB_URL: str
    DATABASE_NAME: str = "workout_analyzer"
    
    # Google Cloud
    GOOGLE_CLOUD_PROJECT_ID: str
    GOOGLE_CLOUD_STORAGE_BUCKET: str
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # FastAPI
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Gemini AI
    GOOGLE_API_KEY: str
    
    # Application
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # File Upload
    MAX_FILE_SIZE: int = 100  # MB
    ALLOWED_VIDEO_EXTENSIONS: str = "mp4,avi,mov,mkv"
    
    # MediaPipe
    CONFIDENCE_THRESHOLD: float = 0.5
    DETECTION_CONFIDENCE: float = 0.5
    TRACKING_CONFIDENCE: float = 0.5
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()