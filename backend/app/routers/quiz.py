from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import logging
from datetime import datetime, timezone

from app.models.quiz import (
    QuizGenerateRequest, QuizSubmission, QuizResponse, 
    QuizResults, QuizModel
)
# Correctly importing the factory function
from app.services.quiz_generator import get_quiz_generator_service
from app.core.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate/{doc_id}", response_model=QuizResponse)
async def generate_quiz(
    doc_id: str,
    request: QuizGenerateRequest = QuizGenerateRequest(),
    user_id: str = Depends(get_current_user_id)
):
    """Generate a quiz from document using Bloom's Taxonomy"""
    try:
        # FIX: Get an instance of the quiz generator service
        quiz_generator = get_quiz_generator_service()
        quiz = await quiz_generator.generate_quiz(
            document_id=doc_id,
            user_id=user_id,
            request=request
        )
        
        return QuizResponse(
            success=True,
            data={
                "quiz_id": quiz.quiz_id,
                "document_id": quiz.document_id,
                "title": quiz.title,
                "description": quiz.description,
                "total_questions": len(quiz.questions),
                "total_points": quiz.total_points,
                "time_limit": quiz.time_limit,
                "attempts_allowed": quiz.attempts_allowed,
                "bloom_distribution": quiz.bloom_distribution,
                "questions": [
                    {
                        "question_id": q.get("questionId") or q.get("question_id"),
                        "question": q.get("question"),
                        "options": q.get("options"),
                        "bloom_level": q.get("bloomLevel") or q.get("bloom_level"),
                        "difficulty": q.get("difficulty"),
                        "points": q.get("points")
                    }
                    for q in quiz.questions
                ]
            },
            message=f"สร้างแบบทดสอบ {len(quiz.questions)} ข้อสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get quiz by ID"""
    try:
        # FIX: Get an instance of the quiz generator service
        quiz_generator = get_quiz_generator_service()
        quiz = await quiz_generator.get_quiz(quiz_id)
        
        if not quiz:
            raise HTTPException(status_code=404, detail="ไม่พบแบบทดสอบที่ร้องขอ")
        
        return QuizResponse(
            success=True,
            data={
                "quiz_id": quiz.quiz_id,
                "document_id": quiz.document_id,
                "title": quiz.title,
                "description": quiz.description,
                "total_questions": len(quiz.questions),
                "total_points": quiz.total_points,
                "time_limit": quiz.time_limit,
                "attempts_allowed": quiz.attempts_allowed,
                "bloom_distribution": quiz.bloom_distribution,
                "questions": [
                    {
                        "question_id": q.get("questionId") or q.get("question_id"),
                        "question": q.get("question"),
                        "options": q.get("options"),
                        "bloom_level": q.get("bloomLevel") or q.get("bloom_level"),
                        "difficulty": q.get("difficulty"),
                        "points": q.get("points")
                    }
                    for q in quiz.questions
                ]
            },
            message="ดึงข้อมูลแบบทดสอบสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงข้อมูลแบบทดสอบ")

@router.post("/{quiz_id}/submit", response_model=QuizResponse)
async def submit_quiz(
    quiz_id: str,
    submission: QuizSubmission,
    user_id: str = Depends(get_current_user_id)
):
    """Submit quiz answers and get results"""
    try:
        # FIX: Get an instance of the quiz generator service
        quiz_generator = get_quiz_generator_service()
        results = await quiz_generator.submit_quiz(
            quiz_id=quiz_id,
            user_id=user_id,
            submission=submission
        )
        
        return QuizResponse(
            success=True,
            data={
                "attempt_id": results.attemptId,
                "quiz_id": results.quizId,
                "score": results.score,
                "total_points": results.totalPoints,
                "percentage": results.percentage,
                "time_taken": results.timeTaken,
                "bloom_scores": results.bloomScores,
                "question_results": results.questionResults,
                "recommendations": results.recommendations
            },
            message=f"ส่งแบบทดสอบสำเร็จ คะแนน {results.percentage:.1f}%",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error submitting quiz: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{quiz_id}/results/{attempt_id}", response_model=QuizResponse)
async def get_quiz_results(
    quiz_id: str,
    attempt_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get specific quiz attempt results"""
    try:
        # FIX: Get an instance of the quiz generator service
        quiz_generator = get_quiz_generator_service()
        attempt = await quiz_generator.get_quiz_results(attempt_id, user_id)
        
        if not attempt:
            raise HTTPException(status_code=404, detail="ไม่พบผลการทำแบบทดสอบที่ร้องขอ")
        
        return QuizResponse(
            success=True,
            data=attempt.dict(), # Directly return the model dict
            message="ดึงผลการทำแบบทดสอบสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz results: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงผลการทำแบบทดสอบ")

@router.get("/history/{doc_id}", response_model=QuizResponse)
async def get_quiz_history(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get quiz history for a document"""
    try:
        # FIX: Get an instance of the quiz generator service
        quiz_generator = get_quiz_generator_service()
        history = await quiz_generator.get_quiz_history(
            user_id=user_id,
            document_id=doc_id
        )
        
        return QuizResponse(
            success=True,
            data={
                "document_id": doc_id,
                "total_attempts": len(history),
                "attempts": history
            },
            message="ดึงประวัติการทำแบบทดสอบสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting quiz history: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงประวัติการทำแบบทดสอบ")

@router.get("/user/history", response_model=QuizResponse)
async def get_user_quiz_history(
    user_id: str = Depends(get_current_user_id)
):
    """Get all quiz history for user"""
    try:
        # FIX: Get an instance of the quiz generator service
        quiz_generator = get_quiz_generator_service()
        history = await quiz_generator.get_quiz_history(user_id=user_id)
        
        return QuizResponse(
            success=True,
            data={
                "user_id": user_id,
                "total_attempts": len(history),
                "attempts": history
            },
            message="ดึงประวัติการทำแบบทดสอบทั้งหมดสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting user quiz history: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงประวัติการทำแบบทดสอบ")

@router.get("/{quiz_id}/analytics", response_model=QuizResponse)
async def get_quiz_analytics(
    quiz_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get analytics for a specific quiz"""
    try:
        # FIX: Get an instance of the quiz generator service
        quiz_generator = get_quiz_generator_service()
        analytics = await quiz_generator.get_quiz_analytics(quiz_id)
        
        return QuizResponse(
            success=True,
            data={
                "quiz_id": quiz_id,
                "analytics": analytics
            },
            message="ดึงข้อมูลวิเคราะห์แบบทดสอบสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting quiz analytics: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงข้อมูลวิเคราะห์")

@router.delete("/{quiz_id}", response_model=QuizResponse)
async def delete_quiz(
    quiz_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a quiz and all associated attempts"""
    try:
        # FIX: Get an instance of the quiz generator service
        quiz_generator = get_quiz_generator_service()
        success = await quiz_generator.delete_quiz(quiz_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="ไม่พบแบบทดสอบที่ร้องขอ")
        
        return QuizResponse(
            success=True,
            data={"quiz_id": quiz_id},
            message="ลบแบบทดสอบสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting quiz: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการลบแบบทดสอบ")

@router.get("/{quiz_id}/difficulty/{level}", response_model=QuizResponse) 
async def get_questions_by_difficulty(
    quiz_id: str,
    level: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get questions filtered by difficulty level"""
    try:
        # FIX: Get an instance of the quiz generator service
        quiz_generator = get_quiz_generator_service()
        quiz = await quiz_generator.get_quiz(quiz_id)
        
        if not quiz:
            raise HTTPException(status_code=404, detail="ไม่พบแบบทดสอบที่ร้องขอ")
        
        filtered_questions = [
            {
                "question_id": q.get("questionId") or q.get("question_id"),
                "question": q.get("question"),
                "options": q.get("options"),
                "bloom_level": q.get("bloomLevel") or q.get("bloom_level"),
                "difficulty": q.get("difficulty"),
                "points": q.get("points")
            }
            for q in quiz.questions if q.get("difficulty") == level
        ]
        
        return QuizResponse(
            success=True,
            data={
                "quiz_id": quiz_id,
                "difficulty_level": level,
                "total_questions": len(filtered_questions),
                "questions": filtered_questions
            },
            message=f"ดึงคำถามระดับ {level} สำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting questions by difficulty: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงคำถาม")

@router.get("/{quiz_id}/bloom/{level}", response_model=QuizResponse)
async def get_questions_by_bloom_level(
    quiz_id: str,
    level: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get questions filtered by Bloom's taxonomy level"""
    try:
        # FIX: Get an instance of the quiz generator service
        quiz_generator = get_quiz_generator_service()
        quiz = await quiz_generator.get_quiz(quiz_id)
        
        if not quiz:
            raise HTTPException(status_code=404, detail="ไม่พบแบบทดสอบที่ร้องขอ")
        
        filtered_questions = [
            {
                "question_id": q.get("questionId") or q.get("question_id"),
                "question": q.get("question"),
                "options": q.get("options"),
                "bloom_level": q.get("bloomLevel") or q.get("bloom_level"),
                "difficulty": q.get("difficulty"),
                "points": q.get("points")
            }
            for q in quiz.questions if q.get("bloomLevel", q.get("bloom_level")) == level
        ]
        
        return QuizResponse(
            success=True,
            data={
                "quiz_id": quiz_id,
                "bloom_level": level,
                "total_questions": len(filtered_questions),
                "questions": filtered_questions
            },
            message=f"ดึงคำถามระดับ {level} สำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting questions by bloom level: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงคำถาม")
