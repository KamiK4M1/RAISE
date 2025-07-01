"""
Common FastAPI dependencies
"""
from typing import Optional
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_db_client
from app.core.auth import get_current_user, get_current_user_id, get_current_user_optional

# Database dependency
async def get_db() -> AsyncIOMotorDatabase:
    """Dependency to get MongoDB database client"""
    return await get_db_client()

# Export authentication dependencies for easy import
get_current_user = get_current_user
get_current_user_id = get_current_user_id  
get_current_user_optional = get_current_user_optional