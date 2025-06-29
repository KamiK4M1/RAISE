from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging
from datetime import datetime

from app.models.analytics import AnalyticsResponse
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_current_user_id() -> str:
    return "temp_user_123"

@router.get("/user", response_model=AnalyticsResponse)
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    user_id: str = Depends(get_current_user_id)
):
    """Get comprehensive analytics for the current user"""
    try:
        analytics = await analytics_service.get_user_analytics(user_id, days)
        
        return AnalyticsResponse(
            success=True,
            data=analytics.dict(),
            message=f"6I-!9%'4@#20+L9IC
I {days} '1%H2*8*3@#G",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail="@4I-4%2C2#6I-!9%'4@#20+L")

@router.get("/document/{doc_id}", response_model=AnalyticsResponse)
async def get_document_analytics(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get analytics for a specific document"""
    try:
        analytics = await analytics_service.get_document_analytics(doc_id)
        
        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])
        
        return AnalyticsResponse(
            success=True,
            data=analytics,
            message="6I-!9%'4@#20+L@-*2#*3@#G",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document analytics: {e}")
        raise HTTPException(status_code=500, detail="@4I-4%2C2#6I-!9%'4@#20+L@-*2#")

@router.get("/progress", response_model=AnalyticsResponse)
async def get_learning_progress(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    user_id: str = Depends(get_current_user_id)
):
    """Get learning progress summary"""
    try:
        analytics = await analytics_service.get_user_analytics(user_id, days)
        
        progress_data = {
            "period_days": days,
            "learning_progress": analytics.learning_progress,
            "study_patterns": analytics.study_patterns,
            "total_activities": (
                analytics.flashcard_stats.get("total_reviews", 0) +
                analytics.quiz_stats.get("total_attempts", 0) +
                analytics.chat_stats.get("total_questions", 0)
            )
        }
        
        return AnalyticsResponse(
            success=True,
            data=progress_data,
            message="6I-!9%'2!7+I22#@#5"#9I*3@#G",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting learning progress: {e}")
        raise HTTPException(status_code=500, detail="@4I-4%2C2#6I-!9%'2!7+I2")

@router.get("/recommendations", response_model=AnalyticsResponse)
async def get_study_recommendations(
    user_id: str = Depends(get_current_user_id)
):
    """Get personalized study recommendations"""
    try:
        analytics = await analytics_service.get_user_analytics(user_id, 30)
        
        return AnalyticsResponse(
            success=True,
            data={
                "recommendations": [rec.dict() for rec in analytics.recommendations],
                "total_recommendations": len(analytics.recommendations)
            },
            message="63A032#@#5"#9I*3@#G",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting study recommendations: {e}")
        raise HTTPException(status_code=500, detail="@4I-4%2C2#63A03")

@router.get("/system", response_model=AnalyticsResponse)
async def get_system_analytics(
    user_id: str = Depends(get_current_user_id)
):
    """Get system-wide analytics"""
    try:
        analytics = await analytics_service.get_system_analytics()
        
        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])
        
        return AnalyticsResponse(
            success=True,
            data=analytics,
            message="6*44#0*3@#G",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system analytics: {e}")
        raise HTTPException(status_code=500, detail="@4I-4%2C2#6*44#0")

@router.post("/track-session", response_model=AnalyticsResponse)
async def track_learning_session(
    activity_type: str,
    document_id: str,
    duration: int,
    details: dict = {},
    user_id: str = Depends(get_current_user_id)
):
    """Track a learning session"""
    try:
        session_id = await analytics_service.track_learning_session(
            user_id=user_id,
            activity_type=activity_type,
            document_id=document_id,
            duration=duration,
            details=details
        )
        
        return AnalyticsResponse(
            success=True,
            data={
                "session_id": session_id,
                "activity_type": activity_type,
                "duration": duration
            },
            message="16@*
12#@#5"#9I*3@#G",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error tracking learning session: {e}")
        raise HTTPException(status_code=400, detail="@4I-4%2C2#16@*
1")