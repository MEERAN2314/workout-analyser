from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.routes import home, live_analysis, recording_analysis, auth, exercises
from app.services.exercise_library import exercise_library
from app.core.init_demo_user import create_demo_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    await exercise_library.initialize()
    # Initialize demo user for testing
    await create_demo_user()
    yield
    # Shutdown
    await close_mongo_connection()

# Create FastAPI app
app = FastAPI(
    title="Workout Analyzer",
    description="AI-powered workout analysis with live and recording capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(home.router, prefix="", tags=["home"])
app.include_router(live_analysis.router, prefix="/live", tags=["live-analysis"])

# Use NEW recording analysis router
from app.api.routes import recording_analysis_new
app.include_router(recording_analysis_new.router, prefix="/recording", tags=["recording-analysis"])

app.include_router(exercises.router, prefix="/exercises", tags=["exercises"])

# Profile management (Phase 4)
from app.api.routes import profile
app.include_router(profile.router, prefix="/profile", tags=["profile"])

# AI Chat (Phase 4 - Week 2)
from app.api.routes import chat
app.include_router(chat.router, prefix="/chat", tags=["ai-chat"])

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )