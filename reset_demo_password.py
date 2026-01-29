#!/usr/bin/env python3
"""
Reset demo user password
Run this to update the demo user's password hash
"""
import asyncio
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.services.auth_service import auth_service

async def main():
    """Reset demo user password"""
    print("🔌 Connecting to database...")
    await connect_to_mongo()
    
    try:
        db = get_database()
        if db is None:
            print("❌ Database not available")
            return
        
        # Find demo user
        user = await db.users.find_one({"username": "demo_user"})
        
        if not user:
            print("❌ Demo user not found")
            return
        
        print(f"✅ Found demo user: {user['username']}")
        
        # Hash new password with updated bcrypt method
        new_password = "demo123456"
        print(f"🔐 Hashing password: {new_password}")
        
        new_hash = auth_service.get_password_hash(new_password)
        print(f"✅ Password hashed successfully")
        
        # Update password in database
        from bson import ObjectId
        result = await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"password_hash": new_hash}}
        )
        
        if result.modified_count > 0:
            print("✅ Demo user password updated successfully!")
            print("\n📝 Login credentials:")
            print("   Username: demo_user")
            print("   Password: demo123456")
        else:
            print("⚠️  Password was not updated (might be the same)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔌 Closing database connection...")
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
