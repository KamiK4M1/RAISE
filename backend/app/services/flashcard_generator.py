import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.database.mongodb import get_flashcards_collection
from app.models.flashcard import FlashcardModel, FlashcardSession, FlashcardStats
from app.services.document_processor import document_processor
from app.services.spaced_repetition import spaced_repetition
from app.core.ai_models import together_ai
from app.core.exceptions import ModelError, DatabaseError

logger = logging.getLogger(__name__)

class FlashcardGenerator:
    def __init__(self):
        pass

    async def generate_flashcards(
        self,
        document_id: str,
        user_id: str,
        count: int = 10,
        difficulty: str = "medium",
        topics: Optional[List[str]] = None
    ) -> List[FlashcardModel]:
        """Generate flashcards from document content"""
        try:
            # Get document
            document = await document_processor.get_document(document_id, user_id)
            if not document:
                raise ModelError("ไม่พบเอกสารที่ร้องขอ")
            
            if document.processing_status != "completed":
                raise ModelError("เอกสารยังไม่ได้ประมวลผลเสร็จสิ้น")
            
            # Prepare content for AI model
            content = document.content
            if topics:
                # Filter content by topics if specified
                topic_content = []
                for chunk in document.chunks:
                    for topic in topics:
                        if topic.lower() in chunk.text.lower():
                            topic_content.append(chunk.text)
                            break
                
                if topic_content:
                    content = "\n".join(topic_content[:10])  # Limit to 10 chunks
            
            # Generate flashcards using AI
            logger.info(f"Generating {count} flashcards for document {document_id}")
            flashcard_data = await together_ai.generate_flashcards(content, count)
            
            # Create flashcard models
            flashcards = []
            collection = await get_flashcards_collection()
            
            for i, card_data in enumerate(flashcard_data):
                card_id = str(uuid.uuid4())
                
                flashcard = FlashcardModel(
                    card_id=card_id,
                    document_id=document_id,
                    question=card_data.get("question", ""),
                    answer=card_data.get("answer", ""),
                    difficulty=card_data.get("difficulty", difficulty),
                    ease_factor=spaced_repetition.default_ease_factor,
                    interval=spaced_repetition.initial_interval,
                    next_review=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # Save to database
                await collection.insert_one(flashcard.dict(by_alias=True, exclude={"id"}))
                flashcards.append(flashcard)
            
            logger.info(f"Generated {len(flashcards)} flashcards successfully")
            return flashcards
            
        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            raise ModelError(f"เกิดข้อผิดพลาดในการสร้างบัตรคำศัพท์: {str(e)}")

    async def get_review_session(
        self,
        document_id: str,
        user_id: str,
        session_size: int = 10
    ) -> FlashcardSession:
        """Get flashcards for review session"""
        try:
            collection = await get_flashcards_collection()
            
            # Get cards due for review
            now = datetime.utcnow()
            cursor = collection.find({
                "document_id": document_id,
                "next_review": {"$lte": now}
            }).sort("next_review", 1).limit(session_size)
            
            cards = []
            async for card_data in cursor:
                card = FlashcardModel(**card_data)
                cards.append(card)
            
            # If not enough due cards, get some upcoming ones
            if len(cards) < session_size:
                remaining = session_size - len(cards)
                cursor = collection.find({
                    "document_id": document_id,
                    "next_review": {"$gt": now}
                }).sort("next_review", 1).limit(remaining)
                
                async for card_data in cursor:
                    card = FlashcardModel(**card_data)
                    cards.append(card)
            
            session_id = str(uuid.uuid4())
            session = FlashcardSession(
                session_id=session_id,
                document_id=document_id,
                cards=cards,
                started_at=datetime.utcnow()
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Error getting review session: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการสร้างเซสชันทบทวน: {str(e)}")

    async def process_answer(
        self,
        card_id: str,
        quality: int,
        time_taken: int,
        user_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process flashcard answer and update review schedule"""
        try:
            collection = await get_flashcards_collection()
            
            # Get current card
            card_data = await collection.find_one({"card_id": card_id})
            if not card_data:
                raise DatabaseError("ไม่พบบัตรคำศัพท์ที่ร้องขอ")
            
            card = FlashcardModel(**card_data)
            
            # Calculate new review parameters
            new_ease_factor, new_interval, next_review = spaced_repetition.calculate_next_review(
                card.ease_factor,
                card.interval,
                quality,
                card.review_count
            )
            
            # Update counters
            new_review_count = card.review_count + 1
            new_correct_count = card.correct_count + (1 if quality >= 3 else 0)
            new_incorrect_count = card.incorrect_count + (1 if quality < 3 else 0)
            
            # Update card in database
            update_data = {
                "ease_factor": new_ease_factor,
                "interval": new_interval,
                "next_review": next_review,
                "review_count": new_review_count,
                "correct_count": new_correct_count,
                "incorrect_count": new_incorrect_count,
                "updated_at": datetime.utcnow()
            }
            
            await collection.update_one(
                {"card_id": card_id},
                {"$set": update_data}
            )
            
            # Determine new difficulty level
            new_difficulty = spaced_repetition.get_difficulty_level(new_ease_factor, new_interval)
            
            # Return response
            is_correct = quality >= 3
            return {
                "card_id": card_id,
                "is_correct": is_correct,
                "quality": quality,
                "time_taken": time_taken,
                "new_interval": new_interval,
                "next_review": next_review,
                "new_difficulty": new_difficulty,
                "accuracy": new_correct_count / new_review_count if new_review_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error processing answer: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการประมวลผลคำตอบ: {str(e)}")

    async def get_review_schedule(
        self,
        document_id: str,
        user_id: str,
        days_ahead: int = 7
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get review schedule for upcoming days"""
        try:
            collection = await get_flashcards_collection()
            
            # Get cards for the next N days
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=days_ahead)
            
            cursor = collection.find({
                "document_id": document_id,
                "next_review": {
                    "$gte": start_date,
                    "$lt": end_date
                }
            }).sort("next_review", 1)
            
            # Group by date
            schedule = {}
            async for card_data in cursor:
                card = FlashcardModel(**card_data)
                review_date = card.next_review.date().isoformat()
                
                if review_date not in schedule:
                    schedule[review_date] = []
                
                schedule[review_date].append({
                    "card_id": card.card_id,
                    "question": card.question[:100] + "..." if len(card.question) > 100 else card.question,
                    "difficulty": card.difficulty,
                    "review_count": card.review_count,
                    "next_review": card.next_review,
                    "urgency": spaced_repetition.get_review_urgency(card.next_review)
                })
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error getting review schedule: {e}")
            return {}

    async def get_flashcard_stats(
        self,
        document_id: str,
        user_id: str
    ) -> FlashcardStats:
        """Get flashcard statistics for a document"""
        try:
            collection = await get_flashcards_collection()
            
            # Get all cards for document
            cursor = collection.find({"document_id": document_id})
            
            total_cards = 0
            due_today = 0
            learning = 0  # Cards with interval < 7
            reviewing = 0  # Cards with interval >= 7
            mastered = 0  # Cards with ease_factor > 2.5 and interval > 30
            ease_factors = []
            
            today = datetime.utcnow().date()
            
            async for card_data in cursor:
                card = FlashcardModel(**card_data)
                total_cards += 1
                ease_factors.append(card.ease_factor)
                
                # Check if due today
                if card.next_review.date() <= today:
                    due_today += 1
                
                # Categorize by learning stage
                if card.interval < 7:
                    learning += 1
                elif card.ease_factor > 2.5 and card.interval > 30:
                    mastered += 1
                else:
                    reviewing += 1
            
            average_ease = sum(ease_factors) / len(ease_factors) if ease_factors else 0
            
            return FlashcardStats(
                total_cards=total_cards,
                due_today=due_today,
                learning=learning,
                reviewing=reviewing,
                mastered=mastered,
                average_ease=average_ease
            )
            
        except Exception as e:
            logger.error(f"Error getting flashcard stats: {e}")
            return FlashcardStats(
                total_cards=0,
                due_today=0,
                learning=0,
                reviewing=0,
                mastered=0,
                average_ease=0.0
            )

    async def reset_card_progress(self, card_id: str) -> bool:
        """Reset a flashcard's progress"""
        try:
            collection = await get_flashcards_collection()
            
            result = await collection.update_one(
                {"card_id": card_id},
                {
                    "$set": {
                        "ease_factor": spaced_repetition.default_ease_factor,
                        "interval": spaced_repetition.initial_interval,
                        "next_review": datetime.utcnow(),
                        "review_count": 0,
                        "correct_count": 0,
                        "incorrect_count": 0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error resetting card progress: {e}")
            return False

    async def delete_flashcard(self, card_id: str) -> bool:
        """Delete a flashcard"""
        try:
            collection = await get_flashcards_collection()
            
            result = await collection.delete_one({"card_id": card_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting flashcard: {e}")
            return False

# Global instance
flashcard_generator = FlashcardGenerator()