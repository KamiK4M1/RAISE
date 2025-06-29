from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        field_schema.update(type="string")
        return field_schema

class UserAnalytics(BaseModel):
    user_id: str
    total_study_time: int  # minutes
    documents_processed: int
    flashcards_created: int
    flashcards_reviewed: int
    quizzes_taken: int
    average_quiz_score: float
    current_streak: int
    longest_streak: int
    bloom_mastery_scores: Dict[str, float]
    weekly_activity: List[int]  # 7 days
    monthly_progress: List[Dict]  # last 12 months
    learning_velocity: float  # cards per hour
    retention_rate: float  # percentage
    preferred_study_time: str  # morning, afternoon, evening, night

class DocumentAnalytics(BaseModel):
    document_id: str
    filename: str
    total_users: int
    total_flashcards: int
    total_quizzes: int
    average_score: float
    completion_rate: float
    difficulty_distribution: Dict[str, int]
    bloom_coverage: Dict[str, int]
    popular_topics: List[str]
    study_time_distribution: Dict[str, int]

class PerformanceMetrics(BaseModel):
    accuracy_trend: List[float]  # last 30 days
    speed_trend: List[float]  # last 30 days
    confidence_trend: List[float]  # last 30 days
    bloom_performance: Dict[str, Dict[str, float]]  # level -> metrics
    subject_performance: Dict[str, float]
    weekly_goals_met: int
    improvement_areas: List[str]
    strengths: List[str]

class LearningInsights(BaseModel):
    optimal_study_duration: int  # minutes
    best_performance_time: str
    recommended_break_frequency: int  # minutes
    learning_style_indicators: Dict[str, float]
    memory_retention_curve: List[float]
    difficulty_comfort_zone: str
    predicted_mastery_timeline: Dict[str, int]  # topic -> days

class ActivityLog(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    activity_type: str
    document_id: Optional[str] = None
    details: Dict = {}
    performance_score: Optional[float] = None
    duration: int = 0  # seconds
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class WeeklyReport(BaseModel):
    week_start: datetime
    week_end: datetime
    total_study_time: int
    flashcards_reviewed: int
    quizzes_completed: int
    average_score: float
    topics_studied: List[str]
    achievements_earned: List[str]
    streak_maintained: bool
    improvement_percentage: float
    next_week_goals: List[str]

class MonthlyReport(BaseModel):
    month: str
    year: int
    total_study_time: int
    documents_completed: int
    flashcards_mastered: int
    quiz_attempts: int
    average_performance: float
    bloom_level_progress: Dict[str, float]
    learning_milestones: List[str]
    areas_of_improvement: List[str]
    recommended_focus: List[str]

class StudyRecommendation(BaseModel):
    type: str
    title: str
    description: str
    priority: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LearningSession(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    activity_type: str
    document_id: str
    duration: int
    details: Dict[str, any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserAnalyticsUpdated(BaseModel):
    user_id: str
    period_days: int
    flashcard_stats: Dict[str, any] = {}
    quiz_stats: Dict[str, any] = {}
    chat_stats: Dict[str, any] = {}
    study_patterns: Dict[str, any] = {}
    learning_progress: Dict[str, any] = {}
    recommendations: List[StudyRecommendation] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class AnalyticsResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str
    timestamp: str