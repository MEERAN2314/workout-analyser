"""
Profile Management Routes
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.dependencies import get_current_user
from app.core.database import get_database
from bson import ObjectId

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

# ============================================================================
# HTML Pages
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def profile_page(request: Request):
    """User profile page - authentication handled client-side"""
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "title": "Profile"
        }
    )

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/api/workouts")
async def get_user_workouts(
    limit: int = 20,
    offset: int = 0,
    exercise: str = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's workout history
    
    - **limit**: Number of results (default: 20, max: 100)
    - **offset**: Pagination offset (default: 0)
    - **exercise**: Filter by exercise name (optional)
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    # Limit validation
    limit = min(limit, 100)
    
    # Build query
    query = {"user_id": ObjectId(current_user["_id"])}
    if exercise:
        query["exercise_name"] = exercise
    
    # Get workouts
    cursor = db.workouts.find(query).sort("created_at", -1).skip(offset).limit(limit)
    workouts = await cursor.to_list(length=limit)
    
    # Get total count
    total = await db.workouts.count_documents(query)
    
    # Convert ObjectId to string
    for workout in workouts:
        workout["_id"] = str(workout["_id"])
        workout["user_id"] = str(workout["user_id"])
    
    return {
        "workouts": workouts,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/api/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """
    Get user's workout statistics
    
    Returns aggregated statistics including:
    - Total workouts
    - Total reps
    - Total calories burned
    - Average accuracy
    - Workout frequency
    - Exercise breakdown
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    user_id = ObjectId(current_user["_id"])
    
    # Get all user workouts
    workouts = await db.workouts.find({"user_id": user_id}).to_list(length=None)
    
    if not workouts:
        return {
            "total_workouts": 0,
            "total_reps": 0,
            "total_calories": 0,
            "average_accuracy": 0,
            "workout_frequency": 0,
            "exercise_breakdown": {},
            "recent_trend": "no_data"
        }
    
    # Calculate statistics
    total_workouts = len(workouts)
    total_reps = sum(w.get("total_reps", 0) for w in workouts)
    total_calories = sum(w.get("calories_burned", 0) for w in workouts)
    
    # Average accuracy
    accuracy_scores = [w.get("accuracy_score", 0) for w in workouts if w.get("accuracy_score")]
    average_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
    
    # Exercise breakdown
    exercise_breakdown = {}
    for workout in workouts:
        exercise = workout.get("exercise_name", "unknown")
        if exercise not in exercise_breakdown:
            exercise_breakdown[exercise] = {
                "count": 0,
                "total_reps": 0,
                "average_accuracy": 0,
                "total_calories": 0
            }
        exercise_breakdown[exercise]["count"] += 1
        exercise_breakdown[exercise]["total_reps"] += workout.get("total_reps", 0)
        exercise_breakdown[exercise]["total_calories"] += workout.get("calories_burned", 0)
        
        if workout.get("accuracy_score"):
            current_avg = exercise_breakdown[exercise]["average_accuracy"]
            count = exercise_breakdown[exercise]["count"]
            new_avg = (current_avg * (count - 1) + workout["accuracy_score"]) / count
            exercise_breakdown[exercise]["average_accuracy"] = new_avg
    
    # Workout frequency (workouts per week)
    if workouts:
        first_workout = min(w.get("created_at", datetime.utcnow()) for w in workouts)
        days_active = (datetime.utcnow() - first_workout).days + 1
        workout_frequency = (total_workouts / days_active) * 7 if days_active > 0 else 0
    else:
        workout_frequency = 0
    
    # Recent trend (last 7 days vs previous 7 days)
    now = datetime.utcnow()
    last_7_days = [w for w in workouts if (now - w.get("created_at", now)).days <= 7]
    prev_7_days = [w for w in workouts if 7 < (now - w.get("created_at", now)).days <= 14]
    
    if len(prev_7_days) > 0:
        if len(last_7_days) > len(prev_7_days):
            recent_trend = "improving"
        elif len(last_7_days) < len(prev_7_days):
            recent_trend = "declining"
        else:
            recent_trend = "stable"
    else:
        recent_trend = "new_user"
    
    return {
        "total_workouts": total_workouts,
        "total_reps": total_reps,
        "total_calories": round(total_calories, 1),
        "average_accuracy": round(average_accuracy * 100, 1),
        "workout_frequency": round(workout_frequency, 1),
        "exercise_breakdown": exercise_breakdown,
        "recent_trend": recent_trend,
        "days_active": days_active if workouts else 0
    }

@router.get("/api/progress")
async def get_progress_data(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Get progress data for charts
    
    - **days**: Number of days to include (default: 30, max: 365)
    
    Returns daily workout data for visualization
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    # Limit validation
    days = min(days, 365)
    
    # Get workouts from last N days
    start_date = datetime.utcnow() - timedelta(days=days)
    workouts = await db.workouts.find({
        "user_id": ObjectId(current_user["_id"]),
        "created_at": {"$gte": start_date}
    }).sort("created_at", 1).to_list(length=None)
    
    # Group by date
    daily_data = {}
    for workout in workouts:
        date = workout.get("created_at", datetime.utcnow()).date().isoformat()
        
        if date not in daily_data:
            daily_data[date] = {
                "date": date,
                "workouts": 0,
                "total_reps": 0,
                "calories": 0,
                "accuracy_scores": []
            }
        
        daily_data[date]["workouts"] += 1
        daily_data[date]["total_reps"] += workout.get("total_reps", 0)
        daily_data[date]["calories"] += workout.get("calories_burned", 0)
        
        if workout.get("accuracy_score"):
            daily_data[date]["accuracy_scores"].append(workout["accuracy_score"])
    
    # Calculate average accuracy per day
    progress_data = []
    for date, data in sorted(daily_data.items()):
        avg_accuracy = sum(data["accuracy_scores"]) / len(data["accuracy_scores"]) if data["accuracy_scores"] else 0
        
        progress_data.append({
            "date": date,
            "workouts": data["workouts"],
            "total_reps": data["total_reps"],
            "calories": round(data["calories"], 1),
            "average_accuracy": round(avg_accuracy * 100, 1)
        })
    
    return {
        "days": days,
        "data": progress_data
    }

@router.get("/api/recent-workouts")
async def get_recent_workouts(
    limit: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's most recent workouts
    
    - **limit**: Number of workouts to return (default: 5, max: 20)
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    # Limit validation
    limit = min(limit, 20)
    
    # Get recent workouts
    cursor = db.workouts.find({
        "user_id": ObjectId(current_user["_id"])
    }).sort("created_at", -1).limit(limit)
    
    workouts = await cursor.to_list(length=limit)
    
    # Convert ObjectId to string
    for workout in workouts:
        workout["_id"] = str(workout["_id"])
        workout["user_id"] = str(workout["user_id"])
    
    return {"workouts": workouts}
