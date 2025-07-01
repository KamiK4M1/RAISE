from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, Dict, List
from datetime import datetime

class User(BaseModel):
    """User model for MongoDB"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    id: str = Field(..., description="User ID")
    name: Optional[str] = Field(None, description="User's display name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    emailVerified: Optional[datetime] = Field(None, description="Email verification timestamp")
    image: Optional[str] = Field(None, description="Profile image URL")
    password: Optional[str] = Field(None, description="Hashed password")
    role: str = Field(default="user", description="User role")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    """Schema for creating a new user"""
    name: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    role: str = Field(default="user")

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""
    id: str
    name: Optional[str]
    email: Optional[str]
    emailVerified: Optional[datetime]
    image: Optional[str]
    role: str
    createdAt: datetime
    updatedAt: datetime

class TokenData(BaseModel):
    """Schema for JWT token data"""
    email: Optional[str] = None
    user_id: Optional[str] = None
    sub: Optional[str] = None  # JWT subject claim

class Token(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    image: Optional[str] = None

class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

# User Progress models - these will be separate collections/models if needed
# since they're not in the main Prisma schema
class UserProgress(BaseModel):
    """User progress tracking (custom model)"""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[str] = None
    userId: str
    documentId: str
    flashcardsReviewed: int = 0
    quizAttempts: int = 0
    averageScore: float = 0.0
    studyTime: int = 0  # minutes
    lastActivity: datetime = Field(default_factory=datetime.utcnow)
    streakDays: int = 0
    bestScore: float = 0.0
    bloomMastery: Dict[str, float] = Field(default_factory=lambda: {
        "remember": 0.0,
        "understand": 0.0,
        "apply": 0.0,
        "analyze": 0.0,
        "evaluate": 0.0,
        "create": 0.0
    })
    learningGoals: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class StudySession(BaseModel):
    """Study session tracking"""
    sessionId: str
    userId: str
    documentId: str
    activityType: str  # flashcards, quiz, chat
    startTime: datetime
    endTime: Optional[datetime] = None
    duration: int = 0  # minutes
    itemsCompleted: int = 0
    performanceScore: float = 0.0

class UserActivity(BaseModel):
    """User activity tracking"""
    userId: str
    activityType: str
    documentId: Optional[str] = None
    sessionDuration: int = 0
    itemsCompleted: int = 0
    performanceData: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LearningRecommendation(BaseModel):
    """Learning recommendations"""
    type: str  # focus_area, review_cards, take_quiz, etc.
    priority: str  # high, medium, low
    title: str
    description: str
    actionUrl: Optional[str] = None
    estimatedTime: int = 0  # minutes