from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime

class QuizQuestion(BaseModel):
    """Quiz question model"""
    questionId: str
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str
    bloomLevel: str  # remember, understand, apply, analyze, evaluate, create
    difficulty: str = "medium"  # easy, medium, hard
    points: int = 1

class QuizModel(BaseModel):
    """Quiz model for MongoDB"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    quiz_id: str = Field(..., description="Quiz ID")
    document_id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Quiz title")
    description: Optional[str] = Field(None, description="Quiz description")
    questions: List[Dict] = Field(..., description="Quiz questions")
    total_points: int = Field(..., description="Total points")
    time_limit: Optional[int] = Field(None, description="Time limit in minutes")
    attempts_allowed: int = Field(default=-1, description="Number of attempts allowed")
    bloom_distribution: Optional[Dict[str, int]] = Field(None, description="Bloom taxonomy distribution")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class QuizAttempt(BaseModel):
    """Quiz attempt model for MongoDB"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    attempt_id: str = Field(..., description="Attempt ID")
    user_id: str = Field(..., description="User ID")
    quiz_id: str = Field(..., description="Quiz ID")
    answers: List[str] = Field(..., description="User answers")
    score: float = Field(..., description="Score achieved")
    total_points: int = Field(..., description="Total possible points")
    percentage: float = Field(..., description="Percentage score")
    time_taken: int = Field(..., description="Time taken in seconds")
    bloom_scores: Dict[str, float] = Field(default_factory=dict, description="Bloom taxonomy scores")
    question_results: List[Dict] = Field(default_factory=list, description="Question-by-question results")
    completed_at: datetime = Field(default_factory=datetime.utcnow)

class QuizGenerateRequest(BaseModel):
    """Request for generating a quiz"""
    questionCount: int = 10
    bloomDistribution: Optional[Dict[str, int]] = None
    difficulty: str = "medium"
    timeLimit: Optional[int] = None
    includeExplanations: bool = True

class QuizSubmission(BaseModel):
    answers: List[str]
    time_taken: int

class QuizResults(BaseModel):
    """Quiz results summary"""
    attemptId: str
    quizId: str
    score: float
    percentage: float
    totalPoints: int
    timeTaken: int
    bloomScores: Dict[str, float]
    questionResults: List[Dict]
    recommendations: List[str]
    
class QuizCreate(BaseModel):
    """Schema for creating a quiz"""
    documentId: str
    title: str
    description: Optional[str] = None
    questions: Dict
    totalPoints: int
    timeLimit: Optional[int] = None
    
class QuizAttemptCreate(BaseModel):
    """Schema for creating a quiz attempt"""
    userId: str
    quizId: str
    answers: Dict
    timeTaken: int

class QuizResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str
    timestamp: str