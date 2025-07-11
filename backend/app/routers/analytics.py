from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime, timezone

from app.services.analytics_service import AnalyticsService, get_analytics_service
from app.services.spaced_repetition import get_spaced_repetition_service
from app.models.analytics import AnalyticsResponse
from app.core.dependencies import get_current_user_id


logger = logging.getLogger(__name__)

router = APIRouter()

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
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
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
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
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
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
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
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
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
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
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
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error tracking learning session: {e}")
        raise HTTPException(status_code=400, detail="Error tracking learning session.")

@router.get("/recent-activity", response_model=AnalyticsResponse)
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of recent activities to return"),
    user_id: str = Depends(get_current_user_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get recent user activities"""
    try:
        activities = await analytics_service.get_recent_activities(user_id, limit)

        return AnalyticsResponse(
            success=True,
            data={"activities": activities, "total": len(activities)},
            message="Recent activities retrieved successfully.",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error getting recent activities: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving recent activities.")

@router.get("/forgetting-curve", response_model=AnalyticsResponse)
async def get_forgetting_curve(
    days_back: int = Query(90, ge=30, le=365, description="Number of days to analyze"),
    user_id: str = Depends(get_current_user_id),
    spaced_repetition_service = Depends(get_spaced_repetition_service)
):
    """Get forgetting curve analysis for user's flashcards"""
    try:
        forgetting_curve = await spaced_repetition_service.analyze_forgetting_curve(user_id, days_back)
        
        return AnalyticsResponse(
            success=True,
            data={
                "forgetting_curve": [
                    {
                        "interval_days": point.interval_days,
                        "retention_rate": point.retention_rate,
                        "review_count": point.review_count,
                        "average_quality": point.average_quality,
                        "confidence_interval": point.confidence_interval
                    }
                    for point in forgetting_curve
                ],
                "analysis_period_days": days_back,
                "total_data_points": len(forgetting_curve)
            },
            message="Forgetting curve analysis retrieved successfully.",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error getting forgetting curve: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving forgetting curve analysis.")

@router.get("/learning-recommendations", response_model=AnalyticsResponse)
async def get_learning_recommendations(
    user_id: str = Depends(get_current_user_id),
    spaced_repetition_service = Depends(get_spaced_repetition_service)
):
    """Get AI-powered learning recommendations"""
    try:
        recommendations = await spaced_repetition_service.generate_learning_recommendations(user_id)
        
        return AnalyticsResponse(
            success=True,
            data={
                "recommendations": [
                    {
                        "type": rec.type,
                        "priority": rec.priority,
                        "title": rec.title,
                        "description": rec.description,
                        "action_items": rec.action_items,
                        "estimated_improvement": rec.estimated_improvement
                    }
                    for rec in recommendations
                ],
                "total_recommendations": len(recommendations)
            },
            message="Learning recommendations retrieved successfully.",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error getting learning recommendations: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving learning recommendations.")

@router.get("/learning-statistics", response_model=AnalyticsResponse)
async def get_learning_statistics(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    user_id: str = Depends(get_current_user_id),
    spaced_repetition_service = Depends(get_spaced_repetition_service)
):
    """Get detailed learning statistics from spaced repetition system"""
    try:
        stats = await spaced_repetition_service.get_learning_statistics(user_id, days_back)
        
        return AnalyticsResponse(
            success=True,
            data={
                "learning_statistics": {
                    "total_reviews": stats.total_reviews,
                    "correct_reviews": stats.correct_reviews,
                    "accuracy_rate": stats.accuracy_rate,
                    "average_ease_factor": stats.average_ease_factor,
                    "total_study_time": stats.total_study_time,
                    "cards_due_today": stats.cards_due_today,
                    "cards_learned_today": stats.cards_learned_today,
                    "retention_rate": stats.retention_rate,
                    "predicted_workload": stats.predicted_workload,
                    "learning_velocity": stats.learning_velocity,
                    "consistency_score": stats.consistency_score
                },
                "analysis_period_days": days_back
            },
            message="Learning statistics retrieved successfully.",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error getting learning statistics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving learning statistics.")

@router.get("/study-schedule", response_model=AnalyticsResponse)
async def get_optimized_study_schedule(
    target_daily_reviews: int = Query(50, ge=10, le=200, description="Target reviews per day"),
    max_new_cards: int = Query(10, ge=0, le=50, description="Maximum new cards per day"),
    available_time_minutes: int = Query(30, ge=15, le=180, description="Available study time in minutes"),
    user_id: str = Depends(get_current_user_id),
    spaced_repetition_service = Depends(get_spaced_repetition_service)
):
    """Get optimized study schedule recommendation"""
    try:
        schedule = await spaced_repetition_service.optimize_study_schedule(
            user_id, target_daily_reviews, max_new_cards, available_time_minutes
        )
        
        return AnalyticsResponse(
            success=True,
            data={
                "optimized_schedule": schedule,
                "parameters": {
                    "target_daily_reviews": target_daily_reviews,
                    "max_new_cards": max_new_cards,
                    "available_time_minutes": available_time_minutes
                }
            },
            message="Optimized study schedule generated successfully.",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error generating study schedule: {e}")
        raise HTTPException(status_code=500, detail="Error generating optimized study schedule.")