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
    """Quiz model matching Prisma schema"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    id: str = Field(..., description="Quiz ID")
    documentId: str = Field(..., description="Document ID")
    title: str = Field(..., description="Quiz title")
    description: Optional[str] = Field(None, description="Quiz description")
    questions: Dict = Field(..., description="Quiz questions (JSON)")
    totalPoints: int = Field(..., description="Total points")
    timeLimit: Optional[int] = Field(None, description="Time limit in minutes")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class QuizAttempt(BaseModel):
    """Quiz attempt model matching Prisma schema"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    id: str = Field(..., description="Attempt ID")
    userId: str = Field(..., description="User ID")
    quizId: str = Field(..., description="Quiz ID")
    answers: Dict = Field(..., description="User answers (JSON)")
    score: float = Field(..., description="Score achieved")
    totalPoints: int = Field(..., description="Total possible points")
    percentage: float = Field(..., description="Percentage score")
    timeTaken: int = Field(..., description="Time taken in seconds")
    completedAt: datetime = Field(default_factory=datetime.utcnow)

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