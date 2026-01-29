"""
Initialize demo user for testing
"""
import asyncio
import logging
from datetime import datetime

from app.core.database import get_database
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

async def create_demo_user():
    """Create demo user if it doesn't exist"""
    try:
        db = get_database()
        if db is None:
            logger.error("Database not available")
            return False
        
        # Check if demo user already exists
        existing_user = await db.users.find_one({"username": "demo_user"})
        
        if existing_user:
            logger.info("Demo user already exists")
            return True
        
        # Create demo user
        demo_data = {
            "username": "demo_user",
            "email": "demo@workoutanalyzer.com",
            "password": "demo123456",
            "full_name": "Demo User",
            "age": 25,
            "height": 175.0,
            "weight": 70.0,
            "fitness_level": "intermediate",
            "goals": ["general_fitness", "strength"]
        }
        
        result = await auth_service.register_user(demo_data)
        logger.info(f"Demo user created successfully: {result}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create demo user: {e}")
        return False

def init_demo_user_sync():
    """Synchronous wrapper for creating demo user"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a task
            asyncio.create_task(create_demo_user())
        else:
            # If no loop is running, run it
            loop.run_until_complete(create_demo_user())
    except Exception as e:
        logger.error(f"Error initializing demo user: {e}")
