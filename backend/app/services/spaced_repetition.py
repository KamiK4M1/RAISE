import math
import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.core.database import get_prisma_client
from app.models.flashcard import FlashcardModel, FlashcardAnswer, FlashcardReview
from app.core.exceptions import DatabaseError
from app.utils.thai_processing import thai_processor

logger = logging.getLogger(__name__)

class ReviewQuality(Enum):
    """SM-2 Quality scale (0-5)"""
    COMPLETE_BLACKOUT = 0      # Complete blackout
    INCORRECT_EASY = 1         # Incorrect response; correct response seems easy to recall
    INCORRECT_HESITANT = 2     # Incorrect response; correct response seems difficult to recall
    CORRECT_DIFFICULT = 3      # Correct response recalled with serious difficulty
    CORRECT_HESITANT = 4       # Correct response after a hesitation
    PERFECT = 5                # Perfect response

class CardStage(Enum):
    """Learning stages for cards"""
    NEW = "new"                # Never studied
    LEARNING = "learning"      # Currently being learned (interval < 1 day)
    REVIEWING = "reviewing"    # In review phase (interval >= 1 day)
    RELEARNING = "relearning"  # Failed and being relearned
    GRADUATED = "graduated"    # Successfully learned (EF > 2.5, interval > 21 days)

@dataclass
class ReviewResult:
    """Result of a single review"""
    card_id: str
    old_ease_factor: float
    new_ease_factor: float
    old_interval: int
    new_interval: int
    next_review: datetime
    quality: int
    time_taken: int
    stage: CardStage
    is_lapse: bool

@dataclass
class LearningStats:
    """Learning statistics for analysis"""
    total_reviews: int
    correct_reviews: int
    accuracy_rate: float
    average_ease_factor: float
    total_study_time: int
    cards_due_today: int
    cards_learned_today: int
    retention_rate: float
    predicted_workload: Dict[str, int]

@dataclass
class ForgettingCurve:
    """Forgetting curve analysis"""
    interval_days: int
    retention_rate: float
    review_count: int
    average_quality: float

class SpacedRepetitionService:
    """
    Complete SM-2 (SuperMemo 2) algorithm implementation with advanced features
    
    The SM-2 algorithm uses the following formula for ease factor calculation:
    EF = EF + (0.1 - (5-q)*(0.08+(5-q)*0.02))
    
    Where:
    - EF is the ease factor
    - q is the quality of response (0-5)
    
    Interval calculation:
    - First repetition: 1 day
    - Second repetition: 6 days  
    - Subsequent repetitions: previous_interval * ease_factor
    """
    
    def __init__(self):
        # SM-2 algorithm constants
        self.MINIMUM_EASE_FACTOR = 1.3
        self.DEFAULT_EASE_FACTOR = 2.5
        self.MAXIMUM_EASE_FACTOR = 4.0
        self.INITIAL_INTERVAL = 1
        self.SECOND_INTERVAL = 6
        self.GRADUATION_INTERVAL = 21  # Days to consider a card "graduated"
        
        # Learning parameters
        self.LEARNING_STEPS = [1, 10, 1440]  # Minutes: 1 min, 10 min, 1 day
        self.RELEARNING_STEPS = [10, 1440]   # Minutes: 10 min, 1 day
        self.LAPSE_THRESHOLD = 3             # Quality below this triggers relearning
        
        # Performance tracking
        self.review_history: List[ReviewResult] = []
        
    async def process_flashcard_answer(
        self, 
        card_id: str, 
        user_id: str, 
        answer: FlashcardAnswer
    ) -> ReviewResult:
        """
        Process a flashcard answer and update the card using SM-2 algorithm
        
        Args:
            card_id: Flashcard ID
            user_id: User ID
            answer: FlashcardAnswer containing quality (0-5) and time taken
            
        Returns:
            ReviewResult with updated parameters
        """
        try:
            # Get current card data
            prisma = await get_prisma_client()
            card = await prisma.flashcard.find_unique(
                where={"id": card_id}
            )
            
            if not card or card.userId != user_id:
                raise DatabaseError(f"Flashcard {card_id} not found for user {user_id}")
            
            # Validate quality score
            if not 0 <= answer.quality <= 5:
                raise ValueError(f"Quality score must be between 0-5, got {answer.quality}")
            
            # Calculate new parameters using SM-2
            old_ease_factor = card.easeFactor
            old_interval = card.interval
            
            new_ease_factor, new_interval, next_review = self._calculate_sm2_parameters(
                ease_factor=old_ease_factor,
                interval=old_interval,
                quality=answer.quality,
                review_count=card.reviewCount
            )
            
            # Determine card stage
            is_lapse = answer.quality < self.LAPSE_THRESHOLD
            stage = self._determine_card_stage(new_ease_factor, new_interval, is_lapse)
            
            # Update card in database
            updated_card = await prisma.flashcard.update(
                where={"id": card_id},
                data={
                    "easeFactor": new_ease_factor,
                    "interval": new_interval,
                    "nextReview": next_review,
                    "reviewCount": card.reviewCount + 1,
                    "updatedAt": datetime.utcnow()
                }
            )
            
            # Create review result
            review_result = ReviewResult(
                card_id=card_id,
                old_ease_factor=old_ease_factor,
                new_ease_factor=new_ease_factor,
                old_interval=old_interval,
                new_interval=new_interval,
                next_review=next_review,
                quality=answer.quality,
                time_taken=answer.timeTaken,
                stage=stage,
                is_lapse=is_lapse
            )
            
            # Record review history
            await self._record_review_history(user_id, review_result)
            
            # Update learning analytics
            await self._update_learning_analytics(user_id, review_result)
            
            logger.info(f"Processed flashcard {card_id}: EF {old_ease_factor:.2f}→{new_ease_factor:.2f}, "
                       f"Interval {old_interval}→{new_interval}, Quality {answer.quality}")
            
            return review_result
            
        except Exception as e:
            logger.error(f"Error processing flashcard answer: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการประมวลผลคำตอบ: {str(e)}")
    
    def _calculate_sm2_parameters(
        self, 
        ease_factor: float, 
        interval: int, 
        quality: int,
        review_count: int
    ) -> Tuple[float, int, datetime]:
        """
        Calculate new parameters using the SM-2 algorithm
        
        Args:
            ease_factor: Current ease factor
            interval: Current interval in days
            quality: Quality of response (0-5)
            review_count: Number of previous reviews
            
        Returns:
            Tuple of (new_ease_factor, new_interval, next_review_date)
        """
        # Calculate new ease factor using SM-2 formula
        # EF = EF + (0.1 - (5-q)*(0.08+(5-q)*0.02))
        ef_delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        new_ease_factor = ease_factor + ef_delta
        
        # Ensure ease factor stays within bounds
        new_ease_factor = max(self.MINIMUM_EASE_FACTOR, 
                             min(self.MAXIMUM_EASE_FACTOR, new_ease_factor))
        
        # Calculate new interval based on SM-2 rules
        if quality < self.LAPSE_THRESHOLD:
            # Failed card - restart learning
            new_interval = 1
        else:
            # Successful recall
            if review_count == 0:
                # First review
                new_interval = self.INITIAL_INTERVAL
            elif review_count == 1:
                # Second review
                new_interval = self.SECOND_INTERVAL
            else:
                # Subsequent reviews: interval * ease_factor
                new_interval = max(1, round(interval * new_ease_factor))
        
        # Apply interval randomization to prevent bunching
        new_interval = self._apply_interval_fuzz(new_interval)
        
        # Calculate next review date
        next_review = datetime.utcnow() + timedelta(days=new_interval)
        
        return new_ease_factor, new_interval, next_review
    
    def _apply_interval_fuzz(self, interval: int) -> int:
        """
        Apply fuzzing to intervals to prevent all cards being due on the same day
        
        Args:
            interval: Base interval in days
            
        Returns:
            Fuzzed interval
        """
        if interval < 2:
            return interval
        
        # Apply ±25% fuzzing for intervals > 1 day
        fuzz_range = max(1, interval * 0.25)
        import random
        fuzz = random.uniform(-fuzz_range, fuzz_range)
        
        return max(1, round(interval + fuzz))
    
    def _determine_card_stage(
        self, 
        ease_factor: float, 
        interval: int, 
        is_lapse: bool
    ) -> CardStage:
        """Determine the learning stage of a card"""
        if is_lapse:
            return CardStage.RELEARNING
        elif interval < 1:
            return CardStage.LEARNING
        elif ease_factor > 2.5 and interval >= self.GRADUATION_INTERVAL:
            return CardStage.GRADUATED
        else:
            return CardStage.REVIEWING
    
    async def get_due_cards(
        self, 
        user_id: str, 
        limit: Optional[int] = None,
        include_learning: bool = True
    ) -> List[FlashcardModel]:
        """
        Get cards that are due for review
        
        Args:
            user_id: User ID
            limit: Maximum number of cards to return
            include_learning: Whether to include cards in learning stage
            
        Returns:
            List of due flashcards sorted by priority
        """
        try:
            prisma = await get_prisma_client()
            
            # Build query filters
            where_conditions = {
                "userId": user_id,
                "nextReview": {"lte": datetime.utcnow()}
            }
            
            # Get due cards
            cards = await prisma.flashcard.find_many(
                where=where_conditions,
                order_by=[
                    {"nextReview": "asc"},  # Oldest due cards first
                    {"easeFactor": "asc"}   # Harder cards first (lower EF)
                ]
            )
            
            # Convert to FlashcardModel objects
            flashcard_models = []
            for card in cards:
                flashcard_model = FlashcardModel(
                    id=card.id,
                    userId=card.userId,
                    documentId=card.documentId,
                    question=card.question,
                    answer=card.answer,
                    difficulty=card.difficulty,
                    easeFactor=card.easeFactor,
                    interval=card.interval,
                    nextReview=card.nextReview,
                    reviewCount=card.reviewCount,
                    createdAt=card.createdAt,
                    updatedAt=card.updatedAt
                )
                flashcard_models.append(flashcard_model)
            
            # Apply prioritization
            prioritized_cards = self._prioritize_cards(flashcard_models)
            
            # Apply limit if specified
            if limit:
                prioritized_cards = prioritized_cards[:limit]
            
            logger.info(f"Found {len(prioritized_cards)} due cards for user {user_id}")
            return prioritized_cards
            
        except Exception as e:
            logger.error(f"Error getting due cards: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการดึงการ์ดที่ถึงกำหนด: {str(e)}")
    
    def _prioritize_cards(self, cards: List[FlashcardModel]) -> List[FlashcardModel]:
        """
        Prioritize cards based on multiple factors:
        1. Overdue cards (highest priority)
        2. Cards with lower ease factor (more difficult)
        3. Cards not reviewed recently
        """
        now = datetime.utcnow()
        
        def priority_score(card: FlashcardModel) -> float:
            # Calculate how overdue the card is (in days)
            overdue_days = (now - card.nextReview).total_seconds() / 86400
            
            # Base priority from being overdue
            priority = max(0, overdue_days)
            
            # Boost priority for difficult cards (lower ease factor)
            difficulty_boost = (3.0 - card.easeFactor) * 10
            
            # Boost priority for cards with fewer reviews
            review_boost = max(0, 10 - card.reviewCount)
            
            return priority + difficulty_boost + review_boost
        
        # Sort by priority score (descending)
        return sorted(cards, key=priority_score, reverse=True)
    
    async def get_learning_statistics(self, user_id: str) -> LearningStats:
        """
        Get comprehensive learning statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            LearningStats object with detailed analytics
        """
        try:
            prisma = await get_prisma_client()
            
            # Get all user's cards
            cards = await prisma.flashcard.find_many(
                where={"userId": user_id}
            )
            
            # Get review history for today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_reviews = await self._get_reviews_since(user_id, today_start)
            
            # Calculate basic stats
            total_cards = len(cards)
            due_today = len([c for c in cards if c.nextReview <= datetime.utcnow()])
            
            # Calculate accuracy and ease factor stats
            if cards:
                avg_ease_factor = statistics.mean([c.easeFactor for c in cards])
                total_reviews = sum([c.reviewCount for c in cards])
            else:
                avg_ease_factor = self.DEFAULT_EASE_FACTOR
                total_reviews = 0
            
            # Calculate retention rate from recent reviews
            retention_rate = await self._calculate_retention_rate(user_id)
            
            # Predict future workload
            predicted_workload = await self._predict_workload(user_id)
            
            # Calculate accuracy from today's reviews
            if today_reviews:
                correct_today = len([r for r in today_reviews if r.quality >= self.LAPSE_THRESHOLD])
                accuracy_rate = correct_today / len(today_reviews)
                total_study_time = sum([r.time_taken for r in today_reviews])
                cards_learned_today = len(set([r.card_id for r in today_reviews]))
            else:
                accuracy_rate = 0.0
                total_study_time = 0
                cards_learned_today = 0
            
            return LearningStats(
                total_reviews=total_reviews,
                correct_reviews=len([r for r in today_reviews if r.quality >= self.LAPSE_THRESHOLD]),
                accuracy_rate=accuracy_rate,
                average_ease_factor=avg_ease_factor,
                total_study_time=total_study_time,
                cards_due_today=due_today,
                cards_learned_today=cards_learned_today,
                retention_rate=retention_rate,
                predicted_workload=predicted_workload
            )
            
        except Exception as e:
            logger.error(f"Error calculating learning statistics: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการคำนวณสถิติการเรียนรู้: {str(e)}")
    
    async def analyze_forgetting_curve(
        self, 
        user_id: str, 
        days_back: int = 30
    ) -> List[ForgettingCurve]:
        """
        Analyze forgetting curve patterns for the user
        
        Args:
            user_id: User ID
            days_back: Number of days to analyze
            
        Returns:
            List of ForgettingCurve data points
        """
        try:
            # Get review history
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            reviews = await self._get_reviews_since(user_id, cutoff_date)
            
            # Group reviews by interval ranges
            interval_groups = {
                1: [],      # 1 day
                3: [],      # 2-3 days  
                7: [],      # 4-7 days
                14: [],     # 8-14 days
                30: [],     # 15-30 days
                90: [],     # 31-90 days
                365: []     # 91+ days
            }
            
            for review in reviews:
                # Find appropriate interval group
                if review.old_interval <= 1:
                    interval_groups[1].append(review)
                elif review.old_interval <= 3:
                    interval_groups[3].append(review)
                elif review.old_interval <= 7:
                    interval_groups[7].append(review)
                elif review.old_interval <= 14:
                    interval_groups[14].append(review)
                elif review.old_interval <= 30:
                    interval_groups[30].append(review)
                elif review.old_interval <= 90:
                    interval_groups[90].append(review)
                else:
                    interval_groups[365].append(review)
            
            # Calculate forgetting curve points
            curve_points = []
            for interval_days, group_reviews in interval_groups.items():
                if group_reviews:
                    successful_reviews = [r for r in group_reviews if r.quality >= self.LAPSE_THRESHOLD]
                    retention_rate = len(successful_reviews) / len(group_reviews)
                    avg_quality = statistics.mean([r.quality for r in group_reviews])
                    
                    curve_points.append(ForgettingCurve(
                        interval_days=interval_days,
                        retention_rate=retention_rate,
                        review_count=len(group_reviews),
                        average_quality=avg_quality
                    ))
            
            # Sort by interval
            curve_points.sort(key=lambda x: x.interval_days)
            
            logger.info(f"Analyzed forgetting curve with {len(curve_points)} data points")
            return curve_points
            
        except Exception as e:
            logger.error(f"Error analyzing forgetting curve: {e}")
            return []
    
    async def suggest_difficulty_adjustment(
        self, 
        user_id: str, 
        card_id: str
    ) -> Optional[str]:
        """
        Suggest difficulty adjustment based on performance
        
        Args:
            user_id: User ID
            card_id: Card ID to analyze
            
        Returns:
            Suggested difficulty level or None
        """
        try:
            # Get card's review history
            reviews = await self._get_card_review_history(user_id, card_id)
            
            if len(reviews) < 3:  # Need at least 3 reviews for meaningful analysis
                return None
            
            # Calculate performance metrics
            recent_reviews = reviews[-5:]  # Last 5 reviews
            avg_quality = statistics.mean([r.quality for r in recent_reviews])
            avg_time = statistics.mean([r.time_taken for r in recent_reviews])
            
            # Get current card
            prisma = await get_prisma_client()
            card = await prisma.flashcard.find_unique(where={"id": card_id})
            
            if not card:
                return None
            
            current_difficulty = card.difficulty
            
            # Suggest adjustments based on performance
            if avg_quality >= 4.5 and avg_time < 5:  # Very good performance
                if current_difficulty == "easy":
                    return None  # Already at easiest
                elif current_difficulty == "medium":
                    return "easy"
                elif current_difficulty == "hard":
                    return "medium"
            elif avg_quality <= 2.5 or avg_time > 30:  # Poor performance
                if current_difficulty == "hard":
                    return None  # Already at hardest
                elif current_difficulty == "medium":
                    return "hard"
                elif current_difficulty == "easy":
                    return "medium"
            
            return None  # No adjustment needed
            
        except Exception as e:
            logger.error(f"Error suggesting difficulty adjustment: {e}")
            return None
    
    async def optimize_study_schedule(
        self, 
        user_id: str, 
        target_daily_reviews: int = 50,
        max_new_cards: int = 10
    ) -> Dict[str, Any]:
        """
        Optimize study schedule to balance learning and retention
        
        Args:
            user_id: User ID
            target_daily_reviews: Target number of reviews per day
            max_new_cards: Maximum new cards to introduce per day
            
        Returns:
            Optimized schedule recommendations
        """
        try:
            # Get current workload
            stats = await self.get_learning_statistics(user_id)
            due_cards = await self.get_due_cards(user_id)
            
            # Calculate current load
            current_due = len(due_cards)
            overdue_cards = len([c for c in due_cards if c.nextReview < datetime.utcnow()])
            
            # Predict future workload
            workload_prediction = await self._predict_workload(user_id, days_ahead=7)
            
            # Generate recommendations
            recommendations = {
                "current_status": {
                    "cards_due_today": current_due,
                    "overdue_cards": overdue_cards,
                    "average_ease_factor": stats.average_ease_factor,
                    "retention_rate": stats.retention_rate
                },
                "daily_targets": {
                    "reviews_today": min(current_due, target_daily_reviews),
                    "new_cards_today": max_new_cards if current_due < target_daily_reviews * 0.8 else 0,
                    "study_time_estimate": self._estimate_study_time(min(current_due, target_daily_reviews))
                },
                "schedule_optimization": {
                    "morning_reviews": int(target_daily_reviews * 0.6),
                    "evening_reviews": int(target_daily_reviews * 0.4),
                    "break_frequency": "every_10_cards",
                    "session_length": "20_minutes"
                },
                "workload_prediction": workload_prediction,
                "recommendations": self._generate_study_recommendations(stats, current_due, target_daily_reviews)
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error optimizing study schedule: {e}")
            return {}
    
    def _estimate_study_time(self, num_cards: int) -> int:
        """Estimate study time in minutes for given number of cards"""
        # Average 30 seconds per card including thinking time
        return max(1, (num_cards * 30) // 60)
    
    def _generate_study_recommendations(
        self, 
        stats: LearningStats, 
        current_due: int, 
        target_reviews: int
    ) -> List[str]:
        """Generate personalized study recommendations"""
        recommendations = []
        
        if current_due > target_reviews * 1.5:
            recommendations.append("คุณมีการ์ดค้างเยอะ ควรเน้นทบทวนการ์ดเก่าก่อน")
        
        if stats.retention_rate < 0.8:
            recommendations.append("อัตราการจำได้ต่ำ ควรลดการ์ดใหม่และเน้นทบทวน")
        
        if stats.average_ease_factor < 2.0:
            recommendations.append("การ์ดส่วนใหญ่ยาก ควรทบทวนบ่อยขึ้น")
        
        if stats.accuracy_rate > 0.9:
            recommendations.append("ผลงานดีมาก! สามารถเพิ่มการ์ดใหม่ได้")
        
        return recommendations
    
    async def _record_review_history(self, user_id: str, review: ReviewResult):
        """Record review in history for analytics"""
        # In a production system, this would be stored in a dedicated review history table
        # For now, we'll keep it in memory
        self.review_history.append(review)
        
        # Keep only last 1000 reviews to prevent memory issues
        if len(self.review_history) > 1000:
            self.review_history = self.review_history[-1000:]
    
    async def _update_learning_analytics(self, user_id: str, review: ReviewResult):
        """Update learning analytics based on review"""
        # This would update user learning patterns, streaks, etc.
        # Implementation depends on your analytics requirements
        pass
    
    async def _get_reviews_since(self, user_id: str, since: datetime) -> List[ReviewResult]:
        """Get review history since a specific date"""
        # This would query a review history table in production
        # For now, return from memory
        return [r for r in self.review_history if r.card_id]  # Placeholder
    
    async def _get_card_review_history(self, user_id: str, card_id: str) -> List[ReviewResult]:
        """Get review history for a specific card"""
        return [r for r in self.review_history if r.card_id == card_id]
    
    async def _calculate_retention_rate(self, user_id: str, days_back: int = 7) -> float:
        """Calculate retention rate over the last N days"""
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        recent_reviews = await self._get_reviews_since(user_id, cutoff)
        
        if not recent_reviews:
            return 1.0  # Default to perfect retention if no data
        
        successful = len([r for r in recent_reviews if r.quality >= self.LAPSE_THRESHOLD])
        return successful / len(recent_reviews)
    
    async def _predict_workload(self, user_id: str, days_ahead: int = 7) -> Dict[str, int]:
        """Predict workload for the next N days"""
        try:
            prisma = await get_prisma_client()
            
            # Get all user's cards
            cards = await prisma.flashcard.find_many(
                where={"userId": user_id}
            )
            
            # Predict daily workload
            workload = {}
            base_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            for i in range(days_ahead):
                target_date = base_date + timedelta(days=i)
                next_date = target_date + timedelta(days=1)
                
                due_count = len([
                    c for c in cards 
                    if target_date <= c.nextReview < next_date
                ])
                
                workload[f"day_{i+1}"] = due_count
            
            return workload
            
        except Exception as e:
            logger.error(f"Error predicting workload: {e}")
            return {}

# Global instance
spaced_repetition = SpacedRepetitionService()