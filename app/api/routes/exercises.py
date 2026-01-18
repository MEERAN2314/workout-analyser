from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.exercise_library import exercise_library
from app.models.workout import Exercise

router = APIRouter()

@router.get("/", response_model=List[Exercise])
async def get_exercises(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    search: Optional[str] = Query(None, description="Search exercises by name or description")
):
    """Get list of available exercises with optional filters"""
    try:
        if search:
            exercises = await exercise_library.search_exercises(search)
        elif category:
            exercises = await exercise_library.get_exercises_by_category(category)
        elif difficulty:
            exercises = await exercise_library.get_exercises_by_difficulty(difficulty)
        else:
            exercises = await exercise_library.get_all_exercises()
        
        return exercises
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving exercises: {str(e)}")

@router.get("/{exercise_name}", response_model=Exercise)
async def get_exercise(exercise_name: str):
    """Get detailed exercise information by name"""
    try:
        exercise = await exercise_library.get_exercise(exercise_name)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        return exercise
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving exercise: {str(e)}")

@router.get("/categories/list")
async def get_categories():
    """Get list of all exercise categories"""
    try:
        categories = exercise_library.get_exercise_categories()
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving categories: {str(e)}")

@router.get("/difficulties/list")
async def get_difficulties():
    """Get list of all difficulty levels"""
    try:
        difficulties = exercise_library.get_difficulty_levels()
        return {"difficulties": difficulties}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving difficulties: {str(e)}")

@router.post("/", response_model=Exercise)
async def create_exercise(exercise: Exercise):
    """Create a new exercise (admin functionality)"""
    try:
        # Check if exercise already exists
        existing = await exercise_library.get_exercise(exercise.name)
        if existing:
            raise HTTPException(status_code=400, detail="Exercise already exists")
        
        success = await exercise_library.add_exercise(exercise)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create exercise")
        
        return exercise
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating exercise: {str(e)}")

@router.put("/{exercise_name}", response_model=Exercise)
async def update_exercise(exercise_name: str, exercise: Exercise):
    """Update an existing exercise (admin functionality)"""
    try:
        # Check if exercise exists
        existing = await exercise_library.get_exercise(exercise_name)
        if not existing:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        success = await exercise_library.update_exercise(exercise_name, exercise)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update exercise")
        
        return exercise
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating exercise: {str(e)}")

@router.delete("/{exercise_name}")
async def delete_exercise(exercise_name: str):
    """Delete an exercise (admin functionality)"""
    try:
        # Check if exercise exists
        existing = await exercise_library.get_exercise(exercise_name)
        if not existing:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        success = await exercise_library.delete_exercise(exercise_name)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete exercise")
        
        return {"message": f"Exercise '{exercise_name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting exercise: {str(e)}")