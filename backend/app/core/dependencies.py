"""
Common FastAPI dependencies
"""
from typing import Optional
from fastapi import Depends
from app.core.database import get_prisma_client
from app.core.auth import get_current_user, get_current_user_id, get_current_user_optional
from prisma import Prisma

# Database dependency
async def get_db() -> Prisma:
    """Dependency to get Prisma database client"""
    return await get_prisma_client()

# Export authentication dependencies for easy import
get_current_user = get_current_user
get_current_user_id = get_current_user_id  
get_current_user_optional = get_current_user_optional