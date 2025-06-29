from pydantic import BaseModel, Field
from typing import Optional, Dict, List
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

class UserProgress(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    document_id: str
    flashcards_reviewed: int = 0
    quiz_attempts: int = 0
    average_score: float = 0.0
    study_time: int = 0  # minutes
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    streak_days: int = 0
    best_score: float = 0.0
    bloom_mastery: Dict[str, float] = {
        "remember": 0.0,
        "understand": 0.0,
        "apply": 0.0,
        "analyze": 0.0,
        "evaluate": 0.0,
        "create": 0.0
    }
    learning_goals: List[str] = []
    achievements: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class StudySession(BaseModel):
    session_id: str
    user_id: str
    document_id: str
    activity_type: str  # flashcards, quiz, chat
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: int = 0  # minutes
    items_completed: int = 0
    performance_score: float = 0.0

class UserActivity(BaseModel):
    user_id: str
    activity_type: str
    document_id: Optional[str] = None
    session_duration: int = 0
    items_completed: int = 0
    performance_data: Dict = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LearningRecommendation(BaseModel):
    type: str  # focus_area, review_cards, take_quiz, etc.
    priority: str  # high, medium, low
    title: str
    description: str
    action_url: Optional[str] = None
    estimated_time: int = 0  # minutes