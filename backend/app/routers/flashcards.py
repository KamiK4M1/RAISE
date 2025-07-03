from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import logging
from datetime import datetime, timezone

from app.models.flashcard import (
    FlashcardGenerateRequest,
    FlashcardTopicRequest,
    FlashcardAnswer,
    FlashcardResponse
)
from app.models.document import DocumentAPIResponse
from app.services.flashcard_service import flashcard_service
from app.services.flashcard_generator import flashcard_generator
# FIX 1: Import the getter function instead of the class
from app.services.spaced_repetition import get_spaced_repetition_service
from app.core.auth import get_current_user_id, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate/{doc_id}", response_model=DocumentAPIResponse)
async def generate_flashcards(
    doc_id: str,
    request: FlashcardGenerateRequest = FlashcardGenerateRequest(),
    user_id: str = Depends(get_current_user_id)
):
    """Generate flashcards from document"""
    try:
        flashcards = await flashcard_generator.generate_flashcards(
            document_id=doc_id,
            user_id=user_id,
            count=request.count,
            difficulty=request.difficulty,
            topics=request.topics
        )
        
        return DocumentAPIResponse(
            success=True,
            data={
                "document_id": doc_id,
                "flashcards_generated": len(flashcards),
                "flashcards": [
                    {
                        "card_id": card.id,
                        "question": card.question,
                        "answer": card.answer,
                        "difficulty": card.difficulty
                    }
                    for card in flashcards
                ]
            },
            message=f"สร้างบัตรคำศัพท์ {len(flashcards)} ใบสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/generate-from-topic", response_model=DocumentAPIResponse)
async def generate_flashcards_from_topic(
    request: FlashcardTopicRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Generate flashcards from topic"""
    try:
        flashcards = await flashcard_generator.generate_flashcards_from_topic(
            topic=request.topic,
            user_id=user_id,
            count=request.count,
            difficulty=request.difficulty
        )
        
        return DocumentAPIResponse(
            success=True,
            data={
                "topic": request.topic,
                "document_id": flashcards[0].document_id if flashcards else None,
                "flashcards_generated": len(flashcards),
                "flashcards": [
                    {
                        "card_id": card.id,
                        "document_id": card.document_id,
                        "question": card.question,
                        "answer": card.answer,
                        "difficulty": card.difficulty
                    }
                    for card in flashcards
                ]
            },
            message=f"สร้างบัตรคำศัพท์ {len(flashcards)} ใบจากหัวข้อ '{request.topic}' สำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error generating flashcards from topic: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session/{doc_id}", response_model=DocumentAPIResponse)
async def get_review_session(
    doc_id: str,
    session_size: int = 10,
    user_id: str = Depends(get_current_user_id)
):
    """Get flashcards for review session"""
    try:
        session = await flashcard_generator.get_review_session(
            document_id=doc_id,
            user_id=user_id,
            session_size=session_size
        )
        
        # FIX 2: Get an instance of the spaced repetition service
        spaced_repetition = get_spaced_repetition_service()
        
        return DocumentAPIResponse(
            success=True,
            data={
                "session_id": session.session_id,
                "total_cards": len(session.flashcards),
                "started_at": session.started_at,
                "cards": [
                    {
                        "card_id": card.id,
                        "question": card.question,
                        "answer": card.answer,
                        "difficulty": card.difficulty,
                        "review_count": card.reviewCount,
                        "next_review": card.nextReview,
                        # This call will now work correctly
                        "urgency": spaced_repetition.get_review_urgency(card.nextReview)
                    }
                    for card in session.flashcards
                ]
            },
            message=f"เซสชันทบทวน {len(session.flashcards)} บัตรพร้อมแล้ว",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting review session: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/answer", response_model=DocumentAPIResponse)
async def submit_flashcard_answer(
    answer: FlashcardAnswer,
    user_id: str = Depends(get_current_user_id)
):
    """Submit answer for a flashcard"""
    try:
        result = await flashcard_generator.process_answer(
            card_id=answer.card_id,
            quality=answer.quality,
            time_taken=answer.time_taken,
            user_answer=answer.user_answer
        )
        
        return DocumentAPIResponse(
            success=True,
            data=result,
            message="ประมวลผลคำตอบสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error processing flashcard answer: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/review-schedule/{doc_id}", response_model=DocumentAPIResponse)
async def get_review_schedule(
    doc_id: str,
    days_ahead: int = 7,
    user_id: str = Depends(get_current_user_id)
):
    """Get review schedule for upcoming days"""
    try:
        schedule = await flashcard_generator.get_review_schedule(
            document_id=doc_id,
            user_id=user_id,
            days_ahead=days_ahead
        )
        
        return DocumentAPIResponse(
            success=True,
            data={
                "document_id": doc_id,
                "days_ahead": days_ahead,
                "schedule": schedule
            },
            message="ดึงตารางทบทวนสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting review schedule: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงตารางทบทวน")

@router.get("/stats/{doc_id}", response_model=DocumentAPIResponse)
async def get_flashcard_stats(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get flashcard statistics"""
    try:
        stats = await flashcard_generator.get_flashcard_stats(
            document_id=doc_id,
            user_id=user_id
        )
        
        return DocumentAPIResponse(
            success=True,
            data={
                "document_id": doc_id,
                "stats": stats.dict()
            },
            message="ดึงสถิติบัตรคำศัพท์สำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting flashcard stats: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงสถิติ")

@router.post("/{card_id}/reset", response_model=DocumentAPIResponse)
async def reset_flashcard(
    card_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Reset flashcard progress"""
    try:
        success = await flashcard_generator.reset_card_progress(card_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="ไม่พบบัตรคำศัพท์ที่ร้องขอ")
        
        return DocumentAPIResponse(
            success=True,
            data={"card_id": card_id},
            message="รีเซ็ตความคืบหน้าบัตรคำศัพท์สำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting flashcard: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการรีเซ็ตบัตรคำศัพท์")

@router.delete("/{card_id}", response_model=DocumentAPIResponse)
async def delete_flashcard(
    card_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a flashcard"""
    try:
        success = await flashcard_generator.delete_flashcard(card_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="ไม่พบบัตรคำศัพท์ที่ร้องขอ")
        
        return DocumentAPIResponse(
            success=True,
            data={"card_id": card_id},
            message="ลบบัตรคำศัพท์สำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting flashcard: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการลบบัตรคำศัพท์")

@router.post("/batch-answer", response_model=DocumentAPIResponse)
async def submit_batch_answers(
    answers: List[FlashcardAnswer],
    user_id: str = Depends(get_current_user_id)
):
    """Submit multiple flashcard answers at once"""
    try:
        results = []
        
        for answer in answers:
            result = await flashcard_generator.process_answer(
                card_id=answer.card_id,
                quality=answer.quality,
                time_taken=answer.time_taken,
                user_answer=answer.user_answer
            )
            results.append(result)
        
        return DocumentAPIResponse(
            success=True,
            data={
                "total_processed": len(results),
                "results": results
            },
            message=f"ประมวลผลคำตอบ {len(results)} ข้อสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error processing batch answers: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/all", response_model=DocumentAPIResponse)
async def get_all_user_flashcards(
    skip: int = 0,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id)
):
    """Get all flashcards for the current user"""
    try:
        flashcards = await flashcard_generator.get_user_flashcards(
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        flashcard_data = []
        for card in flashcards:
            flashcard_data.append({
                "card_id": card.id,
                "document_id": card.document_id,
                "question": card.question,
                "answer": card.answer,
                "difficulty": card.difficulty,
                "next_review": card.nextReview,
                "review_count": card.reviewCount,
                "created_at": card.createdAt
            })
        
        return DocumentAPIResponse(
            success=True,
            data={
                "flashcards": flashcard_data,
                "total": len(flashcard_data)
            },
            message=f"ดึงแฟลชการ์ด {len(flashcard_data)} ใบสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting user flashcards: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving flashcards")