from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class Flashcard(BaseModel):
    """Flashcard model for MongoDB"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    id: str = Field(..., description="Flashcard ID")
    user_id: str = Field(..., description="User ID")
    document_id: str = Field(..., description="Document ID")
    question: str = Field(..., description="Flashcard question")
    answer: str = Field(..., description="Flashcard answer")
    difficulty: str = Field(default="medium", description="Difficulty level")
    easeFactor: float = Field(default=2.5, description="SM-2 ease factor")
    interval: int = Field(default=1, description="Days until next review")
    nextReview: datetime = Field(default_factory=datetime.utcnow, description="Next review date")
    reviewCount: int = Field(default=0, description="Number of reviews")
    correctCount: int = Field(default=0, description="Number of correct answers")
    incorrectCount: int = Field(default=0, description="Number of incorrect answers")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class FlashcardGenerateRequest(BaseModel):
    """Request for generating flashcards"""
    count: Optional[int] = 10
    difficulty: Optional[str] = "medium"
    topics: Optional[List[str]] = Field(default_factory=list)

class FlashcardTopicRequest(BaseModel):
    """Request for generating flashcards from a topic"""
    topic: str = Field(..., description="Topic to generate flashcards for")
    count: Optional[int] = 10
    difficulty: Optional[str] = "medium"
    
class FlashcardCreate(BaseModel):
    """Schema for creating a flashcard"""
    document_id: str
    question: str
    answer: str
    difficulty: str = "medium"
    
class FlashcardAnswer(BaseModel):
    """Answer submission model"""
    card_id: str
    user_answer: Optional[str] = None
    quality: Optional[int] = None
    time_taken: Optional[int] = None

class FlashcardUpdate(BaseModel):
    """Schema for updating a flashcard"""
    question: Optional[str] = None
    answer: Optional[str] = None
    difficulty: Optional[str] = None

class FlashcardReview(BaseModel):
    """Flashcard review submission"""
    is_correct: bool
    quality: Optional[int] = None  # 0-5 (SM-2 algorithm)
    time_taken: Optional[int] = None  # seconds

class FlashcardResponse(BaseModel):
    """Flashcard response model"""
    id: str
    user_id: str
    document_id: str
    question: str
    answer: str
    difficulty: str
    easeFactor: float
    interval: int
    nextReview: datetime
    reviewCount: int
    correctCount: int
    incorrectCount: int
    createdAt: datetime
    updatedAt: datetime

class FlashcardStats(BaseModel):
    """Flashcard statistics"""
    total_cards: int
    due_cards: int
    total_reviews: int
    accuracy_percentage: float
    average_ease_factor: float
    average_interval: float

class ReviewSession(BaseModel):
    """Review session data"""
    session_id: str
    flashcards: List[FlashcardResponse]
    started_at: datetime = Field(default_factory=datetime.utcnow)