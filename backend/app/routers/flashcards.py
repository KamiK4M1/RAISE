from fastapi import APIRouter, HTTPException, Depends, Form
from typing import Optional, List
import logging
from datetime import datetime

from app.models.flashcard import (
    FlashcardGenerateRequest,
    FlashcardAnswer,
    FlashcardResponse
)
from app.services.flashcard_generator import flashcard_generator
from app.services.spaced_repetition import SpacedRepetitionService
from app.core.auth import get_current_user_id, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate/{doc_id}", response_model=FlashcardResponse)
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
        
        return FlashcardResponse(
            success=True,
            data={
                "document_id": doc_id,
                "flashcards_generated": len(flashcards),
                "flashcards": [
                    {
                        "card_id": card.card_id,
                        "question": card.question,
                        "answer": card.answer,
                        "difficulty": card.difficulty
                    }
                    for card in flashcards
                ]
            },
            message=f"สร้างบัตรคำศัพท์ {len(flashcards)} ใบสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session/{doc_id}", response_model=FlashcardResponse)
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
        
        return FlashcardResponse(
            success=True,
            data={
                "session_id": session.session_id,
                "document_id": session.document_id,
                "total_cards": len(session.cards),
                "current_index": session.current_index,
                "started_at": session.started_at,
                "cards": [
                    {
                        "card_id": card.card_id,
                        "question": card.question,
                        "answer": card.answer,
                        "difficulty": card.difficulty,
                        "review_count": card.review_count,
                        "next_review": card.next_review,
                        "urgency": spaced_repetition.get_review_urgency(card.next_review)
                    }
                    for card in session.cards
                ]
            },
            message=f"เซสชันทบทวน {len(session.cards)} บัตรพร้อมแล้ว",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting review session: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/answer", response_model=FlashcardResponse)
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
        
        return FlashcardResponse(
            success=True,
            data=result,
            message="ประมวลผลคำตอบสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error processing flashcard answer: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/review-schedule/{doc_id}", response_model=FlashcardResponse)
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
        
        return FlashcardResponse(
            success=True,
            data={
                "document_id": doc_id,
                "days_ahead": days_ahead,
                "schedule": schedule
            },
            message="ดึงตารางทบทวนสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting review schedule: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงตารางทบทวน")

@router.get("/stats/{doc_id}", response_model=FlashcardResponse)
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
        
        return FlashcardResponse(
            success=True,
            data={
                "document_id": doc_id,
                "stats": stats.dict()
            },
            message="ดึงสถิติบัตรคำศัพท์สำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting flashcard stats: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงสถิติ")

@router.post("/{card_id}/reset", response_model=FlashcardResponse)
async def reset_flashcard(
    card_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Reset flashcard progress"""
    try:
        success = await flashcard_generator.reset_card_progress(card_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="ไม่พบบัตรคำศัพท์ที่ร้องขอ")
        
        return FlashcardResponse(
            success=True,
            data={"card_id": card_id},
            message="รีเซ็ตความคืบหน้าบัตรคำศัพท์สำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting flashcard: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการรีเซ็ตบัตรคำศัพท์")

@router.delete("/{card_id}", response_model=FlashcardResponse)
async def delete_flashcard(
    card_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a flashcard"""
    try:
        success = await flashcard_generator.delete_flashcard(card_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="ไม่พบบัตรคำศัพท์ที่ร้องขอ")
        
        return FlashcardResponse(
            success=True,
            data={"card_id": card_id},
            message="ลบบัตรคำศัพท์สำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting flashcard: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการลบบัตรคำศัพท์")

@router.post("/batch-answer", response_model=FlashcardResponse)
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
        
        return FlashcardResponse(
            success=True,
            data={
                "total_processed": len(results),
                "results": results
            },
            message=f"ประมวลผลคำตอบ {len(results)} ข้อสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error processing batch answers: {e}")
        raise HTTPException(status_code=400, detail=str(e))