"""
Authentication Service - JWT-based authentication
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status
import bcrypt
import logging

from app.core.config import settings
from app.core.database import get_database

logger = logging.getLogger(__name__)

class AuthService:
    """Handle user authentication and JWT token management"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            # Ensure password is bytes
            if isinstance(plain_password, str):
                plain_password = plain_password.encode('utf-8')
            if isinstance(hashed_password, str):
                hashed_password = hashed_password.encode('utf-8')
            
            return bcrypt.checkpw(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password - bcrypt has a 72 byte limit"""
        # Bcrypt has a strict 72-byte limit on the UTF-8 encoded password
        # We need to truncate at the BYTE level, not character level
        
        # Convert to bytes
        password_bytes = password.encode('utf-8')
        original_length = len(password_bytes)
        
        # If longer than 72 bytes, truncate
        if len(password_bytes) > 72:
            # Truncate to 72 bytes
            password_bytes = password_bytes[:72]
            logger.warning(f"Password truncated from {original_length} bytes to 72 bytes")
        
        # Hash with bcrypt directly (not through passlib)
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.error(f"Token decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user"""
        db = get_database()
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Truncate password at BYTE level if too long (bcrypt 72 byte limit)
        password = user_data["password"]
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Truncate to 72 bytes and decode back
            password = password_bytes[:72].decode('utf-8', errors='ignore')
            logger.warning(f"Password truncated from {len(password_bytes)} bytes to 72 bytes for user {user_data['username']}")
        
        # Check if user already exists
        existing_user = await db.users.find_one({
            "$or": [
                {"email": user_data["email"]},
                {"username": user_data["username"]}
            ]
        })
        
        if existing_user:
            if existing_user.get("email") == user_data["email"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Hash password
        hashed_password = self.get_password_hash(password)
        
        # Create user document
        user_doc = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password_hash": hashed_password,
            "full_name": user_data.get("full_name", ""),
            "age": user_data.get("age"),
            "height": user_data.get("height"),
            "weight": user_data.get("weight"),
            "fitness_level": user_data.get("fitness_level", "beginner"),
            "goals": user_data.get("goals", []),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Insert user
        result = await db.users.insert_one(user_doc)
        
        logger.info(f"New user registered: {user_data['username']}")
        
        return {
            "user_id": str(result.inserted_id),
            "username": user_data["username"],
            "email": user_data["email"]
        }
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data"""
        db = get_database()
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Find user by username or email
        user = await db.users.find_one({
            "$or": [
                {"username": username},
                {"email": username}
            ]
        })
        
        if not user:
            return None
        
        # Verify password
        if not self.verify_password(password, user["password_hash"]):
            return None
        
        # Update last login
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        logger.info(f"User authenticated: {user['username']}")
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        db = get_database()
        if db is None:
            return None
        
        from bson import ObjectId
        
        try:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            return user
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        db = get_database()
        if db is None:
            return None
        
        user = await db.users.find_one({"username": username})
        return user
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        db = get_database()
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from bson import ObjectId
        
        # Remove fields that shouldn't be updated directly
        update_data.pop("password", None)
        update_data.pop("password_hash", None)
        update_data.pop("username", None)
        update_data.pop("email", None)
        update_data.pop("created_at", None)
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        db = get_database()
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from bson import ObjectId
        
        # Get user
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify old password
        if not self.verify_password(old_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )
        
        # Truncate new password at BYTE level if needed (bcrypt 72 byte limit)
        new_password_bytes = new_password.encode('utf-8')
        if len(new_password_bytes) > 72:
            new_password = new_password_bytes[:72].decode('utf-8', errors='ignore')
            logger.warning(f"New password truncated from {len(new_password_bytes)} bytes to 72 bytes")
        
        # Hash new password
        new_hash = self.get_password_hash(new_password)
        
        # Update password
        try:
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "password_hash": new_hash,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user account"""
        db = get_database()
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from bson import ObjectId
        
        try:
            # Delete user
            result = await db.users.delete_one({"_id": ObjectId(user_id)})
            
            if result.deleted_count > 0:
                # Also delete user's workouts and chat sessions
                await db.workouts.delete_many({"user_id": ObjectId(user_id)})
                await db.chat_sessions.delete_many({"user_id": ObjectId(user_id)})
                await db.chat_messages.delete_many({"user_id": ObjectId(user_id)})
                
                logger.info(f"User deleted: {user_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False

# Global instance
auth_service = AuthService()
