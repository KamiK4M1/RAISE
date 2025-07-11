"""
JWT Authentication and security utilities using MongoDB
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from bson import ObjectId
from app.config import settings
from app.database.mongodb import mongodb_manager

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        logger.info(f"Verifying token with SECRET_KEY length: {len(SECRET_KEY)}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Token verification failed: no 'sub' field in payload")
            return None
        logger.info(f"Token verified successfully for user: {user_id}")
        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
    users_collection = mongodb_manager.get_users_collection()
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

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current user ID only"""
    user = await get_current_user(credentials)
    return user["id"]

# Optional authentication (for endpoints that work with or without auth)
async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Optional authentication - returns None if not authenticated"""
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

async def authenticate_user(email: str, password: str):
    """Authenticate user with email and password"""
    logger.info(f"Attempting to authenticate user: {email}")
    users_collection = mongodb_manager.get_users_collection()
    user = await users_collection.find_one({"email": email})
    
    if not user:
        logger.warning(f"Authentication failed: User with email '{email}' not found.")
        return None
    
    logger.info(f"User '{email}' found. Verifying password.")
    
    stored_password_hash = user.get("password")
    if not stored_password_hash:
        logger.error(f"Authentication failed: User '{email}' has no password stored in the database.")
        return None

    if not verify_password(password, stored_password_hash):
        logger.warning(f"Authentication failed: Invalid password for user '{email}'.")
        return None
    
    logger.info(f"Authentication successful for user: {email}")
    
    # Convert ObjectId to string for consistency
    user["id"] = str(user["_id"])
    del user["_id"]
    
    # Fix field name mapping for UserResponse
    user["emailVerified"] = user.pop("email_verified", None)
    user["createdAt"] = user.pop("created_at", datetime.now(timezone.utc))
    user["updatedAt"] = user.pop("updated_at", datetime.now(timezone.utc))
    
    # Ensure image field exists (it's optional but required by the model)
    if "image" not in user:
        user["image"] = None
    
    return user
