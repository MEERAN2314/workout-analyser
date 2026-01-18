from typing import List, Dict, Optional
from app.models.workout import Exercise
from app.core.database import get_database
import logging

logger = logging.getLogger(__name__)

class ExerciseLibraryService:
    def __init__(self):
        self.exercises_cache = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize exercise library with default exercises"""
        if self.initialized:
            return
        
        try:
            db = get_database()
            if db is None:
                logger.warning("No database connection - using in-memory exercise library")
                self._initialize_memory_library()
                return
            
            # Check if exercises already exist
            existing_count = await db.exercises.count_documents({})
            
            if existing_count == 0:
                # Insert default exercises
                default_exercises = self._get_default_exercises()
                await db.exercises.insert_many([ex.dict(by_alias=True) for ex in default_exercises])
                logger.info(f"Inserted {len(default_exercises)} default exercises")
            
            # Load exercises into cache
            await self._load_exercises_cache()
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing exercise library: {e}")
            self._initialize_memory_library()
    
    def _initialize_memory_library(self):
        """Initialize in-memory exercise library as fallback"""
        exercises = self._get_default_exercises()
        for exercise in exercises:
            self.exercises_cache[exercise.name] = exercise
        self.initialized = True
        logger.info("Initialized in-memory exercise library")
    
    async def _load_exercises_cache(self):
        """Load exercises from database into cache"""
        db = get_database()
        if db is None:
            return
        
        try:
            cursor = db.exercises.find({})
            async for doc in cursor:
                exercise = Exercise(**doc)
                self.exercises_cache[exercise.name] = exercise
            
            logger.info(f"Loaded {len(self.exercises_cache)} exercises into cache")
            
        except Exception as e:
            logger.error(f"Error loading exercises cache: {e}")
    
    def _get_default_exercises(self) -> List[Exercise]:
        """Get default exercise definitions"""
        return [
            Exercise(
                name="push_ups",
                category="upper_body",
                description="Classic upper body exercise targeting chest, triceps, and shoulders",
                instructions=[
                    "Start in a plank position with hands shoulder-width apart",
                    "Lower your body until your chest nearly touches the ground",
                    "Keep your body in a straight line from head to heels",
                    "Push back up to the starting position",
                    "Repeat for desired number of repetitions"
                ],
                target_muscles=["chest", "triceps", "shoulders", "core"],
                difficulty_level="beginner",
                equipment_needed=[],
                key_landmarks=[
                    "left_shoulder", "right_shoulder", 
                    "left_elbow", "right_elbow",
                    "left_wrist", "right_wrist",
                    "left_hip", "right_hip"
                ],
                form_rules={
                    "min_elbow_angle": 70,
                    "max_elbow_angle": 170,
                    "max_elbow_flare": 45,
                    "body_alignment_threshold": 0.1
                }
            ),
            Exercise(
                name="squats",
                category="lower_body",
                description="Fundamental lower body exercise targeting quadriceps, glutes, and hamstrings",
                instructions=[
                    "Stand with feet shoulder-width apart",
                    "Lower your body by bending at the hips and knees",
                    "Keep your chest up and back straight",
                    "Descend until thighs are parallel to the ground",
                    "Push through your heels to return to starting position"
                ],
                target_muscles=["quadriceps", "glutes", "hamstrings", "calves"],
                difficulty_level="beginner",
                equipment_needed=[],
                key_landmarks=[
                    "left_hip", "right_hip",
                    "left_knee", "right_knee",
                    "left_ankle", "right_ankle",
                    "left_shoulder", "right_shoulder"
                ],
                form_rules={
                    "min_knee_angle": 70,
                    "max_knee_angle": 170,
                    "knee_alignment_threshold": 0.05,
                    "depth_threshold": 90
                }
            ),
            Exercise(
                name="bicep_curls",
                category="upper_body",
                description="Isolation exercise targeting the biceps muscles",
                instructions=[
                    "Stand with feet shoulder-width apart",
                    "Hold weights with arms at your sides",
                    "Keep elbows close to your torso",
                    "Curl the weights up by contracting your biceps",
                    "Lower the weights back to starting position with control"
                ],
                target_muscles=["biceps", "forearms"],
                difficulty_level="beginner",
                equipment_needed=["dumbbells"],
                key_landmarks=[
                    "right_shoulder", "right_elbow", "right_wrist",
                    "left_shoulder", "left_elbow", "left_wrist"
                ],
                form_rules={
                    "min_elbow_angle": 30,
                    "max_elbow_angle": 170,
                    "elbow_stability_threshold": 0.1,
                    "full_rom_angle": 45
                }
            ),
            Exercise(
                name="lunges",
                category="lower_body",
                description="Unilateral lower body exercise for leg strength and balance",
                instructions=[
                    "Stand with feet hip-width apart",
                    "Step forward with one leg",
                    "Lower your hips until both knees are bent at 90 degrees",
                    "Keep your front knee over your ankle",
                    "Push back to starting position and repeat"
                ],
                target_muscles=["quadriceps", "glutes", "hamstrings", "calves"],
                difficulty_level="intermediate",
                equipment_needed=[],
                key_landmarks=[
                    "left_hip", "right_hip",
                    "left_knee", "right_knee",
                    "left_ankle", "right_ankle"
                ],
                form_rules={
                    "min_knee_angle": 70,
                    "max_knee_angle": 170,
                    "knee_over_ankle": True,
                    "hip_level_threshold": 0.1
                }
            ),
            Exercise(
                name="planks",
                category="core",
                description="Isometric core strengthening exercise",
                instructions=[
                    "Start in a push-up position",
                    "Lower onto your forearms",
                    "Keep your body in a straight line",
                    "Engage your core muscles",
                    "Hold the position for desired duration"
                ],
                target_muscles=["core", "shoulders", "glutes"],
                difficulty_level="beginner",
                equipment_needed=[],
                key_landmarks=[
                    "left_shoulder", "right_shoulder",
                    "left_hip", "right_hip",
                    "left_ankle", "right_ankle"
                ],
                form_rules={
                    "body_alignment_threshold": 0.05,
                    "hip_sag_threshold": 0.1,
                    "shoulder_stability": True
                }
            )
        ]
    
    async def get_exercise(self, exercise_name: str) -> Optional[Exercise]:
        """Get exercise by name"""
        if not self.initialized:
            await self.initialize()
        
        return self.exercises_cache.get(exercise_name)
    
    async def get_all_exercises(self) -> List[Exercise]:
        """Get all available exercises"""
        if not self.initialized:
            await self.initialize()
        
        return list(self.exercises_cache.values())
    
    async def get_exercises_by_category(self, category: str) -> List[Exercise]:
        """Get exercises filtered by category"""
        if not self.initialized:
            await self.initialize()
        
        return [ex for ex in self.exercises_cache.values() if ex.category == category]
    
    async def get_exercises_by_difficulty(self, difficulty: str) -> List[Exercise]:
        """Get exercises filtered by difficulty level"""
        if not self.initialized:
            await self.initialize()
        
        return [ex for ex in self.exercises_cache.values() if ex.difficulty_level == difficulty]
    
    async def search_exercises(self, query: str) -> List[Exercise]:
        """Search exercises by name or description"""
        if not self.initialized:
            await self.initialize()
        
        query_lower = query.lower()
        results = []
        
        for exercise in self.exercises_cache.values():
            if (query_lower in exercise.name.lower() or 
                query_lower in exercise.description.lower() or
                any(query_lower in muscle.lower() for muscle in exercise.target_muscles)):
                results.append(exercise)
        
        return results
    
    async def add_exercise(self, exercise: Exercise) -> bool:
        """Add new exercise to library"""
        try:
            db = get_database()
            if db is not None:
                await db.exercises.insert_one(exercise.dict(by_alias=True))
            
            # Add to cache
            self.exercises_cache[exercise.name] = exercise
            logger.info(f"Added new exercise: {exercise.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding exercise: {e}")
            return False
    
    async def update_exercise(self, exercise_name: str, updated_exercise: Exercise) -> bool:
        """Update existing exercise"""
        try:
            db = get_database()
            if db is not None:
                await db.exercises.update_one(
                    {"name": exercise_name},
                    {"$set": updated_exercise.dict(by_alias=True)}
                )
            
            # Update cache
            self.exercises_cache[exercise_name] = updated_exercise
            logger.info(f"Updated exercise: {exercise_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating exercise: {e}")
            return False
    
    async def delete_exercise(self, exercise_name: str) -> bool:
        """Delete exercise from library"""
        try:
            db = get_database()
            if db is not None:
                await db.exercises.delete_one({"name": exercise_name})
            
            # Remove from cache
            if exercise_name in self.exercises_cache:
                del self.exercises_cache[exercise_name]
            
            logger.info(f"Deleted exercise: {exercise_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting exercise: {e}")
            return False
    
    def get_exercise_categories(self) -> List[str]:
        """Get list of all exercise categories"""
        if not self.initialized:
            return []
        
        categories = set()
        for exercise in self.exercises_cache.values():
            categories.add(exercise.category)
        
        return sorted(list(categories))
    
    def get_difficulty_levels(self) -> List[str]:
        """Get list of all difficulty levels"""
        return ["beginner", "intermediate", "advanced"]

# Global instance
exercise_library = ExerciseLibraryService()