#!/usr/bin/env python3
"""
Standalone script to create demo user
Run this if you need to manually create the demo user
"""
import asyncio
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.services.auth_service import auth_service

async def main():
    """Create demo user"""
    print("🔌 Connecting to database...")
    await connect_to_mongo()
    
    try:
        db = get_database()
        if db is None:
            print("❌ Database not available")
            return
        
        # Check if demo user already exists
        existing_user = await db.users.find_one({"username": "demo_user"})
        
        if existing_user:
            print("✅ Demo user already exists")
            print(f"   Username: {existing_user['username']}")
            print(f"   Email: {existing_user['email']}")
            return
        
        # Create demo user
        print("👤 Creating demo user...")
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
        
        print("✅ Demo user created successfully!")
        print(f"   User ID: {result['user_id']}")
        print(f"   Username: {result['username']}")
        print(f"   Email: {result['email']}")
        print("\n📝 Login credentials:")
        print("   Username: demo_user")
        print("   Password: demo123456")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("\n🔌 Closing database connection...")
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
