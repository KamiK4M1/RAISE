from pydantic import BaseModel, Field
from typing import List, Optional, Dict
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

class QuizQuestion(BaseModel):
    question_id: str
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    bloom_level: str  # remember, understand, apply, analyze, evaluate, create
    difficulty: str = "medium"  # easy, medium, hard
    points: int = 1

class QuizModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    quiz_id: str
    document_id: str
    title: str
    description: Optional[str] = None
    questions: List[QuizQuestion]
    total_points: int
    time_limit: Optional[int] = None  # minutes
    attempts_allowed: int = 3
    bloom_distribution: Dict[str, int] = {}  # count per bloom level
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class QuizAttempt(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    attempt_id: str
    quiz_id: str
    user_id: str
    answers: List[str]
    score: float
    total_points: int
    percentage: float
    time_taken: int  # seconds
    bloom_scores: Dict[str, float] = {}  # score per bloom level
    question_results: List[Dict] = []  # detailed results per question
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class QuizGenerateRequest(BaseModel):
    question_count: int = 10
    bloom_distribution: Optional[Dict[str, int]] = None
    difficulty: str = "medium"
    time_limit: Optional[int] = None
    include_explanations: bool = True

class QuizSubmission(BaseModel):
    answers: List[str]
    time_taken: int

class QuizResults(BaseModel):
    attempt_id: str
    quiz_id: str
    score: float
    percentage: float
    total_points: int
    time_taken: int
    bloom_scores: Dict[str, float]
    question_results: List[Dict]
    recommendations: List[str]

class QuizResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str
    timestamp: str