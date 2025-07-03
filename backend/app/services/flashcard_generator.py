import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import logging

from app.database.mongodb import mongodb_manager
from app.models.flashcard import Flashcard, ReviewSession, FlashcardStats, FlashcardResponse
from app.services.document_processor import document_processor
from app.services.spaced_repetition import get_spaced_repetition_service # Corrected import
from app.services.rag_service import get_rag_service
from app.core.ai_models import together_ai
from app.core.exceptions import ModelError, DatabaseError

logger = logging.getLogger(__name__)

# Helper function to get the flashcards collection
async def get_flashcards_collection():
    return mongodb_manager.get_flashcards_collection()

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
    ) -> List[Flashcard]:
        """Generate flashcards from document content"""
        try:
            spaced_repetition = get_spaced_repetition_service()
            document = await document_processor.get_document(document_id, user_id)
            if not document:
                raise ModelError("ไม่พบเอกสารที่ร้องขอ")
            
            if document.status != "completed":
                raise ModelError("เอกสารยังไม่ได้ประมวลผลเสร็จสิ้น")
            
            content = document.content
            if topics:
                topic_content = []
                for chunk in document.chunks:
                    for topic in topics:
                        if topic.lower() in chunk.text.lower():
                            topic_content.append(chunk.text)
                            break
                
                if topic_content:
                    content = "\n".join(topic_content[:10])
            
            logger.info(f"Generating {count} flashcards for document {document_id}")
            flashcard_data = await together_ai.generate_flashcards(content, count)
            
            flashcards = []
            # FIX: Call the helper function to get the collection
            collection = await get_flashcards_collection()
            
            for i, card_data in enumerate(flashcard_data):
                card_id = str(uuid.uuid4())
                
                flashcard = Flashcard(
                    id=card_id,
                    user_id=user_id,
                    document_id=document_id,
                    question=card_data.get("question", ""),
                    answer=card_data.get("answer", ""),
                    difficulty=card_data.get("difficulty", difficulty),
                    easeFactor=spaced_repetition.DEFAULT_EASE_FACTOR,
                    interval=spaced_repetition.INITIAL_INTERVAL,
                    nextReview=datetime.now(timezone.utc),
                    createdAt=datetime.now(timezone.utc),
                    updatedAt=datetime.now(timezone.utc)
                )
                
                await collection.insert_one(flashcard.dict(by_alias=True, exclude={"id"}))
                flashcards.append(flashcard)
            
            logger.info(f"Generated {len(flashcards)} flashcards successfully")
            return flashcards
            
        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            raise ModelError(f"เกิดข้อผิดพลาดในการสร้างบัตรคำศัพท์: {str(e)}")

    async def generate_flashcards_from_topic(
        self,
        topic: str,
        user_id: str,
        count: int = 10,
        difficulty: str = "medium"
    ) -> List[Flashcard]:
        """Generate flashcards from a topic using RAG to find similar content from user's documents"""
        try:
            spaced_repetition = get_spaced_repetition_service()
            
            logger.info(f"Generating {count} flashcards for topic: {topic} using RAG")
            
            # Use RAG to find relevant content from user's documents
            try:
                rag_service = get_rag_service()
                rag_result = await rag_service.search_and_generate(
                    query=f"Find information about: {topic}",
                    user_id=user_id,
                    document_ids=None,  # Search across all user documents
                    top_k=10,  # Get top 10 relevant chunks
                    streaming=False
                )
                
                if rag_result and rag_result.context and rag_result.context.context_text:
                    # Use retrieved context to create more informed flashcards
                    context_content = rag_result.context.context_text
                    sources_info = ""
                    if rag_result.context.sources:
                        source_titles = [source.get('document_title', 'Unknown') for source in rag_result.context.sources[:3]]
                        sources_info = f"\n\nBased on content from: {', '.join(source_titles)}"
                    
                    topic_prompt = f"""Create educational flashcards about the topic: {topic}

Use the following relevant content from the user's documents to create accurate and contextual flashcards:

RELEVANT CONTENT:
{context_content}

Generate {count} flashcards with questions and answers that:
- Use specific information from the provided content
- Cover key concepts and definitions found in the content
- Include important facts and details mentioned
- Provide practical applications where relevant
- Use examples and illustrations from the content

Ensure the flashcards are:
- Clear and concise
- Appropriate for {difficulty} difficulty level
- Based on the actual content provided
- Varied in question types (definitions, examples, applications, facts)
- Accurately reflect the information in the source material{sources_info}
"""
                    
                    logger.info(f"Using RAG context for topic '{topic}' with {len(rag_result.context.sources)} sources")
                
                else:
                    # Fallback to general topic-based generation if no relevant content found
                    logger.info(f"No relevant content found for topic '{topic}', using general generation")
                    topic_prompt = f"""Create educational flashcards about the topic: {topic}
            
Generate {count} flashcards with questions and answers that cover:
- Key concepts and definitions
- Important facts and information
- Practical applications
- Examples and illustrations
            
Ensure the flashcards are:
- Clear and concise
- Appropriate for {difficulty} difficulty level
- Educational and informative
- Varied in question types (definitions, examples, applications)
"""
                    
            except Exception as e:
                logger.warning(f"RAG search failed for topic '{topic}': {e}, falling back to general generation")
                # Fallback to general topic-based generation
                topic_prompt = f"""Create educational flashcards about the topic: {topic}
            
Generate {count} flashcards with questions and answers that cover:
- Key concepts and definitions
- Important facts and information
- Practical applications
- Examples and illustrations
            
Ensure the flashcards are:
- Clear and concise
- Appropriate for {difficulty} difficulty level
- Educational and informative
- Varied in question types (definitions, examples, applications)
"""
            
            flashcard_data = await together_ai.generate_flashcards_from_prompt(topic_prompt, count)
            
            flashcards = []
            collection = await get_flashcards_collection()
            
            for i, card_data in enumerate(flashcard_data):
                card_id = str(uuid.uuid4())
                
                flashcard = Flashcard(
                    id=card_id,
                    user_id=user_id,
                    document_id=f"topic_{topic.replace(' ', '_').lower()}",  # Create a pseudo document ID
                    question=card_data.get("question", ""),
                    answer=card_data.get("answer", ""),
                    difficulty=card_data.get("difficulty", difficulty),
                    easeFactor=spaced_repetition.DEFAULT_EASE_FACTOR,
                    interval=spaced_repetition.INITIAL_INTERVAL,
                    nextReview=datetime.now(timezone.utc),
                    createdAt=datetime.now(timezone.utc),
                    updatedAt=datetime.now(timezone.utc)
                )
                
                # Add user_id to the flashcard document
                flashcard_dict = flashcard.dict(by_alias=True, exclude={"id"})
                flashcard_dict["user_id"] = user_id
                flashcard_dict["topic"] = topic
                
                await collection.insert_one(flashcard_dict)
                flashcards.append(flashcard)
            
            logger.info(f"Generated {len(flashcards)} flashcards from topic '{topic}' successfully")
            return flashcards
            
        except Exception as e:
            logger.error(f"Error generating flashcards from topic: {e}")
            raise ModelError(f"เกิดข้อผิดพลาดในการสร้างบัตรคำศัพท์จากหัวข้อ: {str(e)}")

    async def get_review_session(
        self,
        document_id: str,
        user_id: str,
        session_size: int = 10
    ) -> ReviewSession:
        """Get flashcards for review session"""
        try:
            # FIX: Call the helper function to get the collection
            collection = await get_flashcards_collection()
            
            now = datetime.now(timezone.utc)
            cursor = collection.find({
                "document_id": document_id,
                "user_id": user_id,
                "nextReview": {"$lte": now}
            }).sort("nextReview", 1).limit(session_size)
            
            cards = []
            async for card_data in cursor:
                # FIX: Map _id to id field for Pydantic model
                if '_id' in card_data:
                    card_data['id'] = str(card_data['_id'])
                    del card_data['_id']
                card = Flashcard(**card_data)
                cards.append(card)
            
            if len(cards) < session_size:
                remaining = session_size - len(cards)
                cursor = collection.find({
                    "document_id": document_id,
                    "user_id": user_id,
                    "nextReview": {"$gt": now}
                }).sort("nextReview", 1).limit(remaining)
                
                async for card_data in cursor:
                    # FIX: Map _id to id field for Pydantic model
                    if '_id' in card_data:
                        card_data['id'] = str(card_data['_id'])
                        del card_data['_id']
                    card = Flashcard(**card_data)
                    cards.append(card)
            
            session_id = str(uuid.uuid4())
            
            # Convert Flashcard objects to FlashcardResponse objects
            flashcard_responses = []
            for card in cards:
                flashcard_response = FlashcardResponse(
                    id=card.id,
                    user_id=card.user_id,
                    document_id=card.document_id,
                    question=card.question,
                    answer=card.answer,
                    difficulty=card.difficulty,
                    easeFactor=card.easeFactor,
                    interval=card.interval,
                    nextReview=card.nextReview,
                    reviewCount=card.reviewCount,
                    correctCount=card.correctCount,
                    incorrectCount=card.incorrectCount,
                    createdAt=card.createdAt,
                    updatedAt=card.updatedAt
                )
                flashcard_responses.append(flashcard_response)
            
            session = ReviewSession(
                session_id=session_id,
                flashcards=flashcard_responses,
                started_at=datetime.now(timezone.utc)
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Error getting review session: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการสร้างเซสชันทบทวน: {str(e)}")

    async def get_user_flashcards(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Flashcard]:
        """Get all flashcards for a user"""
        try:
            collection = await get_flashcards_collection()
            
            cursor = collection.find({
                "user_id": user_id
            }).sort("created_at", -1).skip(skip).limit(limit)
            
            cards = []
            async for card_data in cursor:
                # FIX: Map _id to id field for Pydantic model
                if '_id' in card_data:
                    card_data['id'] = str(card_data['_id'])
                    del card_data['_id']
                card = Flashcard(**card_data)
                cards.append(card)
            
            return cards
            
        except Exception as e:
            logger.error(f"Error getting user flashcards: {e}")
            return []

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
            
            card_data = await collection.find_one({"card_id": card_id})
            if not card_data:
                raise DatabaseError("ไม่พบบัตรคำศัพท์ที่ร้องขอ")
            
            # FIX: Use the correct Flashcard model
            card = Flashcard(**card_data)
            
            # FIX: Get the spaced_repetition service
            spaced_repetition = get_spaced_repetition_service()
            new_ease_factor, new_interval, next_review = spaced_repetition.calculate_next_review(
                card.ease_factor,
                card.interval,
                quality,
                card.review_count
            )
            
            new_review_count = card.review_count + 1
            new_correct_count = card.correct_count + (1 if quality >= 3 else 0)
            new_incorrect_count = card.incorrect_count + (1 if quality < 3 else 0)
            
            update_data = {
                "ease_factor": new_ease_factor,
                "interval": new_interval,
                "next_review": next_review,
                "review_count": new_review_count,
                "correct_count": new_correct_count,
                "incorrect_count": new_incorrect_count,
                "updated_at": datetime.now(timezone.utc)
            }
            
            await collection.update_one(
                {"card_id": card_id},
                {"$set": update_data}
            )
            
            new_difficulty = spaced_repetition.get_difficulty_level(new_ease_factor, new_interval)
            
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
            
            start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=days_ahead)
            
            cursor = collection.find({
                "document_id": document_id,
                "user_id": user_id,
                "next_review": {
                    "$gte": start_date,
                    "$lt": end_date
                }
            }).sort("next_review", 1)
            
            schedule = {}
            spaced_repetition = get_spaced_repetition_service()
            async for card_data in cursor:
                # FIX: Use the correct Flashcard model
                card = Flashcard(**card_data)
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
            
            cursor = collection.find({
                "document_id": document_id,
                "user_id": user_id
            })
            
            total_cards = 0
            due_today = 0
            learning = 0
            reviewing = 0
            mastered = 0
            ease_factors = []
            
            today = datetime.now(timezone.utc).date()
            
            async for card_data in cursor:
                # FIX: Use the correct Flashcard model
                card = Flashcard(**card_data)
                total_cards += 1
                ease_factors.append(card.ease_factor)
                
                if card.next_review.date() <= today:
                    due_today += 1
                
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
            
            # FIX: Get the spaced_repetition service to access its properties
            spaced_repetition = get_spaced_repetition_service()
            
            result = await collection.update_one(
                {"card_id": card_id},
                {
                    "$set": {
                        "ease_factor": spaced_repetition.DEFAULT_EASE_FACTOR,
                        "interval": spaced_repetition.INITIAL_INTERVAL,
                        "next_review": datetime.now(timezone.utc),
                        "review_count": 0,
                        "correct_count": 0,
                        "incorrect_count": 0,
                        "updated_at": datetime.now(timezone.utc)
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