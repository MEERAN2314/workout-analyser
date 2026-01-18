from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db.database = db.client[settings.DATABASE_NAME]
        
        # Test connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}")
        logger.info("Running without database connection - some features will be limited")
        # Don't raise the exception, just log it
        db.client = None
        db.database = None

async def close_mongo_connection():
    """Close database connection"""
    if db.client is not None:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for better performance"""
    if db.database is None:
        logger.info("Skipping index creation - no database connection")
        return
        
    try:
        # Users collection indexes
        await db.database.users.create_index("email", unique=True)
        await db.database.users.create_index("username", unique=True)
        
        # Workouts collection indexes
        await db.database.workouts.create_index("user_id")
        await db.database.workouts.create_index("created_at")
        await db.database.workouts.create_index([("user_id", 1), ("created_at", -1)])
        
        # Chat sessions indexes
        await db.database.chat_sessions.create_index("user_id")
        await db.database.chat_sessions.create_index("workout_id")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

def get_database():
    """Get database instance"""
    return db.database if db.database is not None else None