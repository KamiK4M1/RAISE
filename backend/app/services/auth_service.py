"""
Authentication Service for RAISE Learning Platform using Prisma

This service handles:
- User registration and login
- JWT token generation and validation
- Password hashing and verification
- User session management
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.core.database import get_prisma_client
from app.core.auth import (
    create_access_token, verify_password, get_password_hash,
    authenticate_user as core_authenticate_user
)
from app.models.user import (
    User, UserCreate, UserLogin, UserResponse, Token, TokenData,
    UserUpdate, PasswordChange
)
from app.core.exceptions import AuthenticationError, UserNotFoundError

logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthService:
    """Service for handling authentication operations using Prisma"""
    
    def __init__(self):
        pass
    
    async def register_user(self, user_data: UserCreate) -> Token:
        """Register a new user"""
        try:
            prisma = await get_prisma_client()
            
            # Check if user already exists
            existing_user = await prisma.user.find_unique(
                where={"email": user_data.email}
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            # Create user
            user = await prisma.user.create(
                data={
                    "name": user_data.name,
                    "email": user_data.email,
                    "password": hashed_password,
                    "role": user_data.role,
                    "emailVerified": None,
                    "image": None
                }
            )
            
            # Generate token
            access_token_expires = timedelta(minutes=1440)  # 24 hours
            access_token = create_access_token(
                data={"sub": user.id, "email": user.email},
                expires_delta=access_token_expires
            )
            
            # Create user response
            user_response = UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                emailVerified=user.emailVerified,
                image=user.image,
                role=user.role,
                createdAt=user.createdAt,
                updatedAt=user.updatedAt
            )
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=1440 * 60,  # 24 hours in seconds
                user=user_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user account"
            )
    
    async def authenticate_user(self, login_data: UserLogin) -> Token:
        """Authenticate user and return token"""
        try:
            # Use core authentication function
            user = await core_authenticate_user(login_data.email, login_data.password)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Generate token
            access_token_expires = timedelta(minutes=1440)  # 24 hours
            access_token = create_access_token(
                data={"sub": user.id, "email": user.email},
                expires_delta=access_token_expires
            )
            
            # Create user response
            user_response = UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                emailVerified=user.emailVerified,
                image=user.image,
                role=user.role,
                createdAt=user.createdAt,
                updatedAt=user.updatedAt
            )
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=1440 * 60,  # 24 hours in seconds
                user=user_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
    
    async def update_user_profile(self, user_id: str, update_data: UserUpdate) -> UserResponse:
        """Update user profile"""
        try:
            prisma = await get_prisma_client()
            
            # Prepare update data
            update_dict = {}
            if update_data.name is not None:
                update_dict["name"] = update_data.name
            if update_data.email is not None:
                update_dict["email"] = update_data.email
            if update_data.image is not None:
                update_dict["image"] = update_data.image
            
            update_dict["updatedAt"] = datetime.utcnow()
            
            # Update user
            user = await prisma.user.update(
                where={"id": user_id},
                data=update_dict
            )
            
            return UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                emailVerified=user.emailVerified,
                image=user.image,
                role=user.role,
                createdAt=user.createdAt,
                updatedAt=user.updatedAt
            )
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            if "Record to update not found" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating profile"
            )
    
    async def change_password(self, user_id: str, password_data: PasswordChange) -> Dict[str, str]:
        """Change user password"""
        try:
            prisma = await get_prisma_client()
            
            # Get current user
            user = await prisma.user.find_unique(
                where={"id": user_id}
            )
            
            if not user or not user.password:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not verify_password(password_data.current_password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Hash new password and update
            new_hashed_password = get_password_hash(password_data.new_password)
            await prisma.user.update(
                where={"id": user_id},
                data={
                    "password": new_hashed_password,
                    "updatedAt": datetime.utcnow()
                }
            )
            
            return {"message": "Password changed successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error changing password"
            )
    
    async def get_user_by_id(self, user_id: str) -> UserResponse:
        """Get user by ID"""
        try:
            prisma = await get_prisma_client()
            
            user = await prisma.user.find_unique(
                where={"id": user_id}
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                emailVerified=user.emailVerified,
                image=user.image,
                role=user.role,
                createdAt=user.createdAt,
                updatedAt=user.updatedAt
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user"
            )

# Global service instance
auth_service = AuthService()