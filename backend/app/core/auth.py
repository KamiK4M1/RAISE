"""
JWT Authentication and security utilities using MongoDB
"""
import logging
from datetime import datetime, timedelta
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
SECRET_KEY = settings.secret_key if hasattr(settings, 'secret_key') else "your-secret-key-here-change-in-production"
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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError:
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
    users_collection = mongodb_manager.get_users_collection()
    user = await users_collection.find_one({"email": email})
    
    if not user:
        return False
    if not user.get("password"):
        return False
    if not verify_password(password, user["password"]):
        return False
    return user