from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class FlashcardModel(BaseModel):
    """Flashcard model matching Prisma schema"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    id: str = Field(..., description="Flashcard ID")
    userId: str = Field(..., description="User ID")
    documentId: str = Field(..., description="Document ID")
    question: str = Field(..., description="Flashcard question")
    answer: str = Field(..., description="Flashcard answer")
    difficulty: str = Field(default="medium", description="Difficulty level")
    easeFactor: float = Field(default=2.5, description="SM-2 ease factor")
    interval: int = Field(default=1, description="Days until next review")
    nextReview: datetime = Field(default_factory=datetime.utcnow, description="Next review date")
    reviewCount: int = Field(default=0, description="Number of reviews")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class FlashcardGenerateRequest(BaseModel):
    """Request for generating flashcards"""
    count: Optional[int] = 10
    difficulty: Optional[str] = "medium"
    topics: Optional[List[str]] = Field(default_factory=list)
    
class FlashcardCreate(BaseModel):
    """Schema for creating a flashcard"""
    userId: str
    documentId: str
    question: str
    answer: str
    difficulty: str = "medium"
    
class FlashcardUpdate(BaseModel):
    """Schema for updating a flashcard"""
    question: Optional[str] = None
    answer: Optional[str] = None
    difficulty: Optional[str] = None
    easeFactor: Optional[float] = None
    interval: Optional[int] = None
    nextReview: Optional[datetime] = None

class FlashcardSession(BaseModel):
    """Flashcard study session"""
    sessionId: str
    documentId: str
    cards: List[FlashcardModel]
    currentIndex: int = 0
    startedAt: datetime = Field(default_factory=datetime.utcnow)

class FlashcardAnswer(BaseModel):
    """Flashcard answer submission"""
    cardId: str
    quality: int  # 0-5 (SM-2 algorithm)
    timeTaken: int  # seconds
    userAnswer: Optional[str] = None

class FlashcardReview(BaseModel):
    """Flashcard review result"""
    cardId: str
    nextReview: datetime
    easeFactor: float
    interval: int

class FlashcardStats(BaseModel):
    """Flashcard statistics"""
    totalCards: int
    dueToday: int
    learning: int
    reviewing: int
    mastered: int
    averageEase: float

class FlashcardResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str
    timestamp: str