from datetime import datetime, timedelta
from typing import Tuple
import math
import logging

logger = logging.getLogger(__name__)

class SpacedRepetitionService:
    """Implements the SM-2 (SuperMemo 2) algorithm for spaced repetition"""
    
    def __init__(self):
        # SM-2 algorithm constants
        self.minimum_ease_factor = 1.3
        self.default_ease_factor = 2.5
        self.initial_interval = 1
        self.second_interval = 6
        
    def calculate_next_review(
        self, 
        ease_factor: float, 
        interval: int, 
        quality: int,
        review_count: int = 0
    ) -> Tuple[float, int, datetime]:
        """
        Calculate next review parameters using SM-2 algorithm
        
        Args:
            ease_factor: Current ease factor (>= 1.3)
            interval: Current interval in days
            quality: Quality of response (0-5)
                    0: Complete blackout
                    1: Incorrect response, but correct one remembered
                    2: Incorrect response, correct one easy to recall
                    3: Correct response recalled with serious difficulty
                    4: Correct response with hesitation
                    5: Perfect response
            review_count: Number of times card has been reviewed
            
        Returns:
            Tuple of (new_ease_factor, new_interval, next_review_date)
        """
        try:
            # Ensure quality is in valid range
            quality = max(0, min(5, quality))
            
            new_ease_factor = ease_factor
            new_interval = interval
            
            if quality >= 3:
                # Correct response
                if review_count == 0:
                    new_interval = self.initial_interval
                elif review_count == 1:
                    new_interval = self.second_interval
                else:
                    new_interval = math.ceil(interval * ease_factor)
                
                # Update ease factor
                new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
                
            else:
                # Incorrect response - reset interval
                new_interval = self.initial_interval
                
            # Ensure ease factor doesn't go below minimum
            new_ease_factor = max(self.minimum_ease_factor, new_ease_factor)
            
            # Calculate next review date
            next_review_date = datetime.utcnow() + timedelta(days=new_interval)
            
            return new_ease_factor, new_interval, next_review_date
            
        except Exception as e:
            logger.error(f"Error calculating next review: {e}")
            # Return safe defaults
            return self.default_ease_factor, self.initial_interval, datetime.utcnow() + timedelta(days=1)
    
    def get_quality_from_performance(
        self, 
        time_taken: int,  # seconds
        is_correct: bool,
        difficulty: str = "medium",
        expected_time: int = 30  # expected time in seconds
    ) -> int:
        """
        Convert performance metrics to SM-2 quality rating
        
        Args:
            time_taken: Time taken to answer in seconds
            is_correct: Whether the answer was correct
            difficulty: Card difficulty level
            expected_time: Expected time for this difficulty level
            
        Returns:
            Quality rating (0-5)
        """
        try:
            if not is_correct:
                # Incorrect answers get 0-2 based on time
                if time_taken <= expected_time:
                    return 2  # Quick wrong answer suggests partial knowledge
                elif time_taken <= expected_time * 2:
                    return 1  # Slow wrong answer
                else:
                    return 0  # Very slow wrong answer (complete blackout)
            
            # Correct answers get 3-5 based on time and difficulty
            difficulty_multipliers = {
                "easy": 0.8,
                "medium": 1.0,
                "hard": 1.3
            }
            
            adjusted_expected_time = expected_time * difficulty_multipliers.get(difficulty, 1.0)
            
            if time_taken <= adjusted_expected_time * 0.5:
                return 5  # Perfect response
            elif time_taken <= adjusted_expected_time:
                return 4  # Good response
            else:
                return 3  # Correct but with difficulty
                
        except Exception as e:
            logger.error(f"Error converting performance to quality: {e}")
            return 3  # Default to middle quality
    
    def get_difficulty_level(self, ease_factor: float, interval: int) -> str:
        """
        Determine difficulty level based on card statistics
        
        Args:
            ease_factor: Current ease factor
            interval: Current interval
            
        Returns:
            Difficulty level: "easy", "medium", or "hard"
        """
        try:
            if ease_factor >= 2.0 and interval >= 30:
                return "easy"
            elif ease_factor >= 1.8 or interval >= 7:
                return "medium"
            else:
                return "hard"
                
        except Exception as e:
            logger.error(f"Error determining difficulty level: {e}")
            return "medium"
    
    def should_review_today(self, next_review: datetime) -> bool:
        """Check if card should be reviewed today"""
        try:
            today = datetime.utcnow().date()
            review_date = next_review.date()
            return review_date <= today
            
        except Exception as e:
            logger.error(f"Error checking review date: {e}")
            return True  # Default to review if error
    
    def get_review_urgency(self, next_review: datetime) -> str:
        """
        Get review urgency level
        
        Returns:
            "overdue", "due", "upcoming", or "future"
        """
        try:
            now = datetime.utcnow()
            time_diff = (next_review - now).total_seconds()
            days_diff = time_diff / (24 * 3600)
            
            if days_diff < -1:
                return "overdue"
            elif days_diff <= 0:
                return "due"
            elif days_diff <= 3:
                return "upcoming"
            else:
                return "future"
                
        except Exception as e:
            logger.error(f"Error getting review urgency: {e}")
            return "due"
    
    def calculate_retention_probability(
        self, 
        ease_factor: float, 
        days_since_review: int
    ) -> float:
        """
        Estimate probability of remembering the card
        Based on exponential forgetting curve
        
        Args:
            ease_factor: Card's ease factor
            days_since_review: Days since last review
            
        Returns:
            Probability between 0 and 1
        """
        try:
            # Simple exponential decay model
            decay_rate = 1.0 / ease_factor
            probability = math.exp(-decay_rate * days_since_review)
            return max(0.0, min(1.0, probability))
            
        except Exception as e:
            logger.error(f"Error calculating retention probability: {e}")
            return 0.5  # Default to 50% if error
    
    def get_optimal_study_session_size(
        self, 
        available_time: int,  # minutes
        average_card_time: int = 1  # minutes per card
    ) -> int:
        """
        Calculate optimal number of cards for study session
        
        Args:
            available_time: Available study time in minutes
            average_card_time: Average time per card in minutes
            
        Returns:
            Recommended number of cards
        """
        try:
            # Account for fatigue - efficiency decreases over time
            if available_time <= 15:
                cards_per_minute = 1.0 / average_card_time
            elif available_time <= 30:
                cards_per_minute = 0.9 / average_card_time
            elif available_time <= 60:
                cards_per_minute = 0.8 / average_card_time
            else:
                cards_per_minute = 0.7 / average_card_time
            
            optimal_cards = int(available_time * cards_per_minute)
            return max(1, optimal_cards)
            
        except Exception as e:
            logger.error(f"Error calculating optimal session size: {e}")
            return 10  # Default session size

# Global instance
spaced_repetition = SpacedRepetitionService()