"""
Authentication Service for RAISE Learning Platform using motor

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

from bson import ObjectId
from app.database.mongodb import Collections, mongodb_manager
from app.core.auth import (
    create_access_token, verify_password, get_password_hash,
    authenticate_user as core_authenticate_user
)
from app.models.user import (
    User, UserCreate, UserLogin, UserResponse, Token,
    UserUpdate, PasswordChange
)
from app.core.exceptions import AuthenticationError, UserNotFoundError

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication operations using motor"""

    def __init__(self):
        self.users_collection = mongodb_manager.get_users_collection()

    async def register_user(self, user_data: UserCreate) -> Token:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = await self.users_collection.find_one(
                {"email": user_data.email}
            )

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Hash password
            hashed_password = get_password_hash(user_data.password)

            # Create user
            user_to_insert = {
                "name": user_data.name,
                "email": user_data.email,
                "password": hashed_password,
                "role": user_data.role,
                "email_verified": None,
                "image": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await self.users_collection.insert_one(user_to_insert)
            user_id = str(result.inserted_id)
            user = await self.users_collection.find_one({"_id": result.inserted_id})
            
            # Convert ObjectId to string for response
            user["id"] = str(user["_id"])
            del user["_id"]


            # Generate token
            access_token_expires = timedelta(minutes=1440)  # 24 hours
            access_token = create_access_token(
                data={"sub": user_id, "email": user['email']},
                expires_delta=access_token_expires
            )

            # Fix field name mapping for UserResponse
            user["emailVerified"] = user.pop("email_verified", None)
            user["createdAt"] = user.pop("created_at")
            user["updatedAt"] = user.pop("updated_at")
            
            # Create user response
            user_response = UserResponse(**user)

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

            # Convert ObjectId to string and fix field names
            user["id"] = str(user["_id"])
            del user["_id"]
            user["emailVerified"] = user.pop("email_verified", None)
            user["createdAt"] = user.pop("created_at")
            user["updatedAt"] = user.pop("updated_at")
            
            # Generate token
            access_token_expires = timedelta(minutes=1440)
            access_token = create_access_token(
                data={"sub": user["id"], "email": user['email']},
                expires_delta=access_token_expires
            )

            # Create user response
            user_response = UserResponse(**user)

            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=1440 * 60,
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
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()

            updated_user = await self.users_collection.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": update_dict},
                return_document=True
            )

            if not updated_user:
                raise UserNotFoundError

            # Convert ObjectId to string and fix field names
            updated_user["id"] = str(updated_user["_id"])
            del updated_user["_id"]
            updated_user["emailVerified"] = updated_user.pop("email_verified", None)
            updated_user["createdAt"] = updated_user.pop("created_at")
            updated_user["updatedAt"] = updated_user.pop("updated_at")

            return UserResponse(**updated_user)

        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating profile"
            )

    async def change_password(self, user_id: str, password_data: PasswordChange) -> Dict[str, str]:
        """Change user password"""
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})

            if not user or not user.get('password'):
                raise UserNotFoundError

            if not verify_password(password_data.current_password, user['password']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )

            new_hashed_password = get_password_hash(password_data.new_password)
            await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password": new_hashed_password, "updated_at": datetime.utcnow()}}
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
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise UserNotFoundError
        
        # Convert ObjectId to string and fix field names
        user["id"] = str(user["_id"])
        del user["_id"]
        user["emailVerified"] = user.pop("email_verified", None)
        user["createdAt"] = user.pop("created_at")
        user["updatedAt"] = user.pop("updated_at")
        
        return UserResponse(**user)

auth_service = AuthService()