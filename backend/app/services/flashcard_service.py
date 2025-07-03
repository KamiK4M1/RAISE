"""
Flashcard Service for RAISE Learning Platform using MongoDB

This service handles:
- Flashcard creation and management
- Spaced repetition algorithm
- Review scheduling and tracking
- Progress analytics
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from bson import ObjectId

from app.database.mongodb import (
    mongodb_manager, Collections,
    create_flashcard_document
)
from app.models.flashcard import (
    Flashcard, FlashcardCreate, FlashcardResponse, FlashcardUpdate,
    FlashcardReview, FlashcardStats, ReviewSession
)
from app.core.exceptions import FlashcardNotFoundError

logger = logging.getLogger(__name__)

class FlashcardService:
    """Service for handling flashcard operations using MongoDB"""

    def __init__(self):
        """
        Service Initializer.
        Collections are now loaded lazily via properties to ensure
        the database is connected before they are accessed.
        """
        pass

    @property
    def flashcards_collection(self):
        """Lazily gets the flashcards collection."""
        return mongodb_manager.get_flashcards_collection()

    @property
    def documents_collection(self):
        """Lazily gets the documents collection."""
        return mongodb_manager.get_documents_collection()

    async def create_flashcard(self, user_id: str, flashcard_data: FlashcardCreate) -> FlashcardResponse:
        """Create a new flashcard"""
        try:
            # Verify document exists and belongs to user
            document = await self.documents_collection.find_one({
                "_id": ObjectId(flashcard_data.document_id),
                "user_id": ObjectId(user_id)
            })
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )

            # Create flashcard document
            flashcard_dict = create_flashcard_document(
                user_id=user_id,
                document_id=flashcard_data.document_id,
                question=flashcard_data.question,
                answer=flashcard_data.answer,
                difficulty=flashcard_data.difficulty
            )
            
            result = await self.flashcards_collection.insert_one(flashcard_dict)
            
            # Get the created flashcard
            flashcard = await self.flashcards_collection.find_one({"_id": result.inserted_id})
            flashcard = self._convert_flashcard_for_response(flashcard)
            
            return FlashcardResponse(**flashcard)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating flashcard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating flashcard"
            )

    async def get_flashcard_by_id(self, flashcard_id: str, user_id: str) -> FlashcardResponse:
        """Get flashcard by ID"""
        try:
            flashcard = await self.flashcards_collection.find_one({
                "_id": ObjectId(flashcard_id),
                "user_id": ObjectId(user_id)
            })
            
            if not flashcard:
                raise FlashcardNotFoundError
            
            flashcard = self._convert_flashcard_for_response(flashcard)
            return FlashcardResponse(**flashcard)

        except FlashcardNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving flashcard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving flashcard"
            )

    async def get_user_flashcards(
        self, 
        user_id: str, 
        document_id: Optional[str] = None,
        skip: int = 0, 
        limit: int = 50
    ) -> List[FlashcardResponse]:
        """Get flashcards for a user, optionally filtered by document"""
        try:
            filter_query = {"user_id": ObjectId(user_id)}
            if document_id:
                filter_query["document_id"] = ObjectId(document_id)

            cursor = self.flashcards_collection.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)
            
            flashcards = []
            async for card in cursor:
                card = self._convert_flashcard_for_response(card)
                flashcards.append(FlashcardResponse(**card))
            
            return flashcards

        except Exception as e:
            logger.error(f"Error retrieving flashcards: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving flashcards"
            )

    async def get_due_flashcards(self, user_id: str, limit: int = 20) -> List[FlashcardResponse]:
        """Get flashcards due for review"""
        try:
            now = datetime.utcnow()
            cursor = self.flashcards_collection.find({
                "user_id": ObjectId(user_id),
                "next_review": {"$lte": now}
            }).sort("next_review", 1).limit(limit)
            
            flashcards = []
            async for card in cursor:
                card = self._convert_flashcard_for_response(card)
                flashcards.append(FlashcardResponse(**card))
            
            return flashcards

        except Exception as e:
            logger.error(f"Error retrieving due flashcards: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving due flashcards"
            )

    async def review_flashcard(self, flashcard_id: str, user_id: str, review: FlashcardReview) -> FlashcardResponse:
        """Review a flashcard and update spaced repetition data"""
        try:
            flashcard = await self.flashcards_collection.find_one({
                "_id": ObjectId(flashcard_id),
                "user_id": ObjectId(user_id)
            })
            
            if not flashcard:
                raise FlashcardNotFoundError

            # Calculate new spaced repetition values
            ease_factor = flashcard["ease_factor"]
            interval = flashcard["interval"]
            review_count = flashcard["review_count"]
            correct_count = flashcard["correct_count"]
            incorrect_count = flashcard["incorrect_count"]

            # Update counts
            review_count += 1
            if review.is_correct:
                correct_count += 1
            else:
                incorrect_count += 1

            # Apply SM-2 algorithm
            if review.is_correct:
                if review_count == 1:
                    interval = 1
                elif review_count == 2:
                    interval = 6
                else:
                    interval = round(interval * ease_factor)
                
                # Update ease factor based on quality (0-5 scale)
                quality = review.quality if review.quality is not None else 3
                ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
                ease_factor = max(1.3, ease_factor)  # Minimum ease factor
            else:
                # Reset interval for incorrect answers
                interval = 1
                ease_factor = max(1.3, ease_factor - 0.2)

            # Calculate next review date
            next_review = datetime.utcnow() + timedelta(days=interval)

            # Update flashcard
            update_data = {
                "ease_factor": ease_factor,
                "interval": interval,
                "next_review": next_review,
                "review_count": review_count,
                "correct_count": correct_count,
                "incorrect_count": incorrect_count,
                "updated_at": datetime.utcnow()
            }

            updated_flashcard = await self.flashcards_collection.find_one_and_update(
                {"_id": ObjectId(flashcard_id)},
                {"$set": update_data},
                return_document=True
            )

            updated_flashcard = self._convert_flashcard_for_response(updated_flashcard)
            return FlashcardResponse(**updated_flashcard)

        except FlashcardNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error reviewing flashcard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error reviewing flashcard"
            )

    async def update_flashcard(
        self, 
        flashcard_id: str, 
        user_id: str, 
        update_data: FlashcardUpdate
    ) -> FlashcardResponse:
        """Update flashcard content"""
        try:
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()

            updated_flashcard = await self.flashcards_collection.find_one_and_update(
                {"_id": ObjectId(flashcard_id), "user_id": ObjectId(user_id)},
                {"$set": update_dict},
                return_document=True
            )

            if not updated_flashcard:
                raise FlashcardNotFoundError

            updated_flashcard = self._convert_flashcard_for_response(updated_flashcard)
            return FlashcardResponse(**updated_flashcard)

        except FlashcardNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating flashcard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating flashcard"
            )

    async def delete_flashcard(self, flashcard_id: str, user_id: str) -> Dict[str, str]:
        """Delete a flashcard"""
        try:
            result = await self.flashcards_collection.delete_one({
                "_id": ObjectId(flashcard_id),
                "user_id": ObjectId(user_id)
            })

            if result.deleted_count == 0:
                raise FlashcardNotFoundError

            return {"message": "Flashcard deleted successfully"}

        except FlashcardNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting flashcard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting flashcard"
            )

    async def get_flashcard_stats(self, user_id: str, document_id: Optional[str] = None) -> FlashcardStats:
        """Get flashcard statistics for user"""
        try:
            filter_query = {"user_id": ObjectId(user_id)}
            if document_id:
                filter_query["document_id"] = ObjectId(document_id)

            # Aggregation pipeline for statistics
            pipeline = [
                {"$match": filter_query},
                {
                    "$group": {
                        "_id": None,
                        "total_cards": {"$sum": 1},
                        "total_reviews": {"$sum": "$review_count"},
                        "total_correct": {"$sum": "$correct_count"},
                        "total_incorrect": {"$sum": "$incorrect_count"},
                        "due_cards": {
                            "$sum": {
                                "$cond": [
                                    {"$lte": ["$next_review", datetime.utcnow()]},
                                    1,
                                    0
                                ]
                            }
                        },
                        "avg_ease_factor": {"$avg": "$ease_factor"},
                        "avg_interval": {"$avg": "$interval"}
                    }
                }
            ]

            result = await self.flashcards_collection.aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                accuracy = 0.0
                if stats["total_reviews"] > 0:
                    accuracy = (stats["total_correct"] / stats["total_reviews"]) * 100

                return FlashcardStats(
                    total_cards=stats["total_cards"],
                    due_cards=stats["due_cards"],
                    total_reviews=stats["total_reviews"],
                    accuracy_percentage=round(accuracy, 2),
                    average_ease_factor=round(stats["avg_ease_factor"], 2),
                    average_interval=round(stats["avg_interval"], 1)
                )
            else:
                return FlashcardStats(
                    total_cards=0,
                    due_cards=0,
                    total_reviews=0,
                    accuracy_percentage=0.0,
                    average_ease_factor=2.5,
                    average_interval=1.0
                )

        except Exception as e:
            logger.error(f"Error getting flashcard stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error getting flashcard statistics"
            )

    def _convert_flashcard_for_response(self, flashcard: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB flashcard to response format"""
        flashcard["id"] = str(flashcard["_id"])
        del flashcard["_id"]
        flashcard["user_id"] = str(flashcard["user_id"])
        flashcard["document_id"] = str(flashcard["document_id"])
        flashcard["createdAt"] = flashcard.pop("created_at")
        flashcard["updatedAt"] = flashcard.pop("updated_at")
        flashcard["easeFactor"] = flashcard.pop("ease_factor")
        flashcard["nextReview"] = flashcard.pop("next_review")
        flashcard["reviewCount"] = flashcard.pop("review_count")
        flashcard["correctCount"] = flashcard.pop("correct_count")
        flashcard["incorrectCount"] = flashcard.pop("incorrect_count")
        return flashcard

# Global flashcard service instance
flashcard_service = FlashcardService()
