"""
Common FastAPI dependencies
"""
from typing import Optional
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_db_client
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from app.core.database import get_db_client
from app.database.mongodb import mongodb_manager
from app.services.auth_service import AuthService
from app.core.auth import verify_token, authenticate_user
from bson import ObjectId
from datetime import timezone, datetime

async def get_users_collection() -> AsyncIOMotorCollection:
    return mongodb_manager.get_users_collection()

async def get_auth_service() -> AuthService:
    """Dependency to get AuthService instance"""
    return AuthService()

# Database dependency
async def get_db() -> AsyncIOMotorDatabase:
    """Dependency to get MongoDB database client"""
    return await get_db_client()

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), users_collection: AsyncIOMotorCollection = Depends(get_users_collection)):
    """Dependency to get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from Bearer scheme
        token = credentials.credentials
        payload = await verify_token(token)
        
        if payload is None:
            raise credentials_exception
            
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    # Get user from database
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    
    if user is None:
        raise credentials_exception
    
    # Convert ObjectId to string for compatibility
    user["id"] = str(user["_id"])
    del user["_id"]

    # Ensure all fields expected by UserResponse are present
    user["emailVerified"] = user.get("email_verified")
    user["createdAt"] = user.get("created_at", datetime.now(timezone.utc))
    user["updatedAt"] = user.get("updated_at", datetime.now(timezone.utc))
    
    return user

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security), users_collection: AsyncIOMotorCollection = Depends(get_users_collection)) -> str:
    """Dependency to get current user ID only"""
    user = await get_current_user(credentials, users_collection)
    return user["id"]

# Optional authentication (for endpoints that work with or without auth)
async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security), users_collection: AsyncIOMotorCollection = Depends(get_users_collection)) -> Optional[dict]:
    """Optional authentication - returns None if not authenticated"""
    try:
        return await get_current_user(credentials, users_collection)
    except HTTPException:
        return None