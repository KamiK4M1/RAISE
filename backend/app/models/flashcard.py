from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class FlashcardModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    card_id: str
    document_id: str
    question: str
    answer: str
    difficulty: str = "medium"  # easy, medium, hard
    ease_factor: float = 2.5  # SM-2 algorithm default
    interval: int = 1  # days until next review
    next_review: datetime = Field(default_factory=datetime.utcnow)
    review_count: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class FlashcardGenerateRequest(BaseModel):
    count: Optional[int] = 10
    difficulty: Optional[str] = "medium"
    topics: Optional[List[str]] = []

class FlashcardSession(BaseModel):
    session_id: str
    document_id: str
    cards: List[FlashcardModel]
    current_index: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)

class FlashcardAnswer(BaseModel):
    card_id: str
    quality: int  # 0-5 (SM-2 algorithm)
    time_taken: int  # seconds
    user_answer: Optional[str] = None

class FlashcardReview(BaseModel):
    card_id: str
    next_review: datetime
    ease_factor: float
    interval: int

class FlashcardStats(BaseModel):
    total_cards: int
    due_today: int
    learning: int
    reviewing: int
    mastered: int
    average_ease: float

class FlashcardResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str
    timestamp: str