from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import timedelta
import logging

from app.models.auth_schemas import (
    UserRegister, UserLogin, Token, RegisterResponse, 
    LoginResponse, UserResponse, PasswordChange, UserUpdate
)
from app.services.auth_service import auth_service
from app.core.dependencies import get_current_user
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

# ============================================================================
# HTML Pages
# ============================================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "title": "Login"}
    )

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "title": "Register"}
    )

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/api/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user
    
    - **username**: Unique username (3-50 chars, alphanumeric + underscore)
    - **email**: Valid email address
    - **password**: Minimum 8 characters, maximum 72 bytes (UTF-8 encoded)
    - **full_name**: Optional full name
    - **age**: Optional age (13-120)
    - **height**: Optional height in cm
    - **weight**: Optional weight in kg
    - **fitness_level**: beginner, intermediate, or advanced
    - **goals**: List of fitness goals
    """
    try:
        # Validate password byte length (bcrypt limit is 72 BYTES, not characters)
        password_bytes = user_data.password.encode('utf-8')
        if len(password_bytes) > 72:
            # Truncate at byte level and decode back
            truncated_password = password_bytes[:72].decode('utf-8', errors='ignore')
            user_data.password = truncated_password
            logger.warning(f"Password truncated from {len(password_bytes)} bytes to 72 bytes during registration")
        
        result = await auth_service.register_user(user_data.model_dump())
        
        return RegisterResponse(
            message="User registered successfully",
            user_id=result["user_id"],
            username=result["username"],
            email=result["email"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/api/login", response_model=LoginResponse)
async def login(credentials: UserLogin):
    """
    Login and receive JWT access token
    
    - **username**: Username or email
    - **password**: User password
    
    Returns JWT token and user information
    """
    # Authenticate user
    user = await auth_service.authenticate_user(
        credentials.username,
        credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": str(user["_id"]), "username": user["username"]},
        expires_delta=access_token_expires
    )
    
    # Prepare user response
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**user)
    )

@router.get("/api/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Requires: Bearer token in Authorization header
    """
    return UserResponse(**current_user)

@router.put("/api/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update current user profile
    
    Requires: Bearer token in Authorization header
    """
    # Update user
    success = await auth_service.update_user(
        current_user["_id"],
        update_data.model_dump(exclude_unset=True)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    # Get updated user
    updated_user = await auth_service.get_user_by_id(current_user["_id"])
    updated_user["_id"] = str(updated_user["_id"])
    updated_user.pop("password_hash", None)
    
    return UserResponse(**updated_user)

@router.post("/api/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """
    Change user password
    
    Requires: Bearer token in Authorization header
    """
    success = await auth_service.change_password(
        current_user["_id"],
        password_data.old_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password"
        )
    
    return {"message": "Password changed successfully"}

@router.delete("/api/me")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """
    Delete user account
    
    Requires: Bearer token in Authorization header
    
    Warning: This will permanently delete the account and all associated data
    """
    success = await auth_service.delete_user(current_user["_id"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )
    
    return {"message": "Account deleted successfully"}

@router.post("/api/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout (client should delete token)
    
    Requires: Bearer token in Authorization header
    """
    # In a stateless JWT system, logout is handled client-side by deleting the token
    # This endpoint is here for completeness and can be used for logging
    logger.info(f"User logged out: {current_user['username']}")
    
    return {"message": "Logged out successfully"}