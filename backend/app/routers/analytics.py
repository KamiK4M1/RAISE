from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from app.services.analytics_service import AnalyticsService, get_analytics_service
from app.models.analytics import AnalyticsResponse


logger = logging.getLogger(__name__)

router = APIRouter()

async def get_current_user_id() -> str:
    return "temp_user_123"

@router.get("/user", response_model=AnalyticsResponse)
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    user_id: str = Depends(get_current_user_id),
    analytics_service_instance: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive analytics for the current user"""
    try:
        analytics = await analytics_service_instance.get_user_analytics(user_id, days)

        return AnalyticsResponse(
            success=True,
            data=analytics.dict(),
            message=f"Analytics for the last {days} days retrieved successfully.",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving user analytics.")

@router.get("/document/{doc_id}", response_model=AnalyticsResponse)
async def get_document_analytics(
    doc_id: str,
    user_id: str = Depends(get_current_user_id),
    analytics_service_instance: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics for a specific document"""
    try:
        analytics = await analytics_service_instance.get_user_analytics(doc_id)

        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])

        return AnalyticsResponse(
            success=True,
            data=analytics,
            message="Document analytics retrieved successfully.",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document analytics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving document analytics.")

@router.get("/progress", response_model=AnalyticsResponse)
async def get_learning_progress(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    user_id: str = Depends(get_current_user_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
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
            message="Learning progress retrieved successfully.",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error getting learning progress: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving learning progress.")

@router.get("/recommendations", response_model=AnalyticsResponse)
async def get_study_recommendations(
    user_id: str = Depends(get_current_user_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
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
            message="Study recommendations retrieved successfully.",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error getting study recommendations: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving study recommendations.")

@router.get("/system", response_model=AnalyticsResponse)
async def get_system_analytics(
    user_id: str = Depends(get_current_user_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get system-wide analytics"""
    try:
        analytics = await analytics_service.get_system_analytics()

        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])

        return AnalyticsResponse(
            success=True,
            data=analytics,
            message="System analytics retrieved successfully.",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system analytics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving system analytics.")

@router.post("/track-session", response_model=AnalyticsResponse)
async def track_learning_session(
    activity_type: str,
    document_id: str,
    duration: int,
    details: dict = {},
    user_id: str = Depends(get_current_user_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
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
            message="Learning session tracked successfully.",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error tracking learning session: {e}")
        raise HTTPException(status_code=400, detail="Error tracking learning session.")