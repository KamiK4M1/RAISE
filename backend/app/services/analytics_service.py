"""
Comprehensive Learning Analytics Engine for RAISE Platform

This module provides advanced analytics and insights for learning data across
flashcards, quizzes, and chat interactions with sophisticated statistical analysis,
machine learning insights, and personalized recommendations.

Features:
- Real-time learning progress calculation
- Knowledge retention analysis using forgetting curves
- Performance prediction models  
- Personalized study recommendations
- Bloom's taxonomy mastery tracking
- Learning velocity and efficiency metrics
- Study pattern analysis
- Weakness identification and strength reinforcement
"""

import asyncio
import math
import statistics
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.database.mongodb import mongodb_manager
from app.models.analytics import UserAnalyticsUpdated as UserAnalytics, LearningSession, StudyRecommendation
from app.services.spaced_repetition import get_spaced_repetition_service, ForgettingCurve

logger = logging.getLogger(__name__)


class LearningStyle(str, Enum):
    """Learning style classification"""
    VISUAL = "visual"
    AUDITORY = "auditory"  
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MIXED = "mixed"


class StudyPattern(str, Enum):
    """Study pattern classification"""
    CRAMMING = "cramming"
    CONSISTENT = "consistent"
    SPORADIC = "sporadic"
    INTENSIVE = "intensive"
    BALANCED = "balanced"


@dataclass
class LearningMetrics:
    """Comprehensive learning metrics"""
    retention_rate: float
    learning_velocity: float
    consistency_score: float
    difficulty_mastery: Dict[str, float]
    bloom_mastery: Dict[str, float]
    optimal_study_time: int
    predicted_performance: float
    learning_efficiency: float
    knowledge_retention_curve: List[Tuple[int, float]]


@dataclass
class PerformanceAnalysis:
    """Performance analysis results"""
    strengths: List[str]
    weaknesses: List[str]
    improvement_areas: List[str]
    mastery_timeline: Dict[str, int]
    confidence_intervals: Dict[str, Tuple[float, float]]
    trend_analysis: Dict[str, str]


@dataclass
class StudyOptimization:
    """Study optimization recommendations"""
    optimal_session_length: int
    best_study_times: List[str]
    recommended_break_frequency: int
    difficulty_progression: str
    content_prioritization: List[str]
    spaced_repetition_schedule: Dict[str, Any]

class AdvancedAnalyticsService:
    """
    Advanced learning analytics service with comprehensive insights and predictions
    
    Provides sophisticated analysis of learning patterns, performance prediction,
    and personalized optimization recommendations using statistical models and
    machine learning techniques.
    """
    
    def __init__(self):
        # Database collections
        self.flashcard_collection = mongodb_manager.get_flashcards_collection()
        self.quiz_collection = mongodb_manager.get_quiz_attempts_collection()
        self.chat_collection = mongodb_manager.get_chat_messages_collection()
        self.document_collection = mongodb_manager.get_documents_collection()
        self.user_collection = mongodb_manager.get_users_collection()
        
        # Get spaced repetition service for advanced analytics
        self.spaced_repetition = get_spaced_repetition_service()
        
        # Analytics parameters
        self.RETENTION_CURVE_INTERVALS = [1, 3, 7, 14, 30, 60, 90, 180]
        self.BLOOM_LEVELS = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
        self.DIFFICULTY_LEVELS = ["easy", "medium", "hard"]
        
        # Machine learning parameters
        self.LEARNING_VELOCITY_WEIGHT = 0.3
        self.CONSISTENCY_WEIGHT = 0.4
        self.ACCURACY_WEIGHT = 0.3
        
    def get_flashcard_collection(self):
        return self.flashcard_collection
    
    def get_quiz_collection(self):
        return self.quiz_collection
    
    def get_chat_collection(self):
        return self.chat_collection
    
    def get_session_collection(self):
        return mongodb_manager.get_collection("learning_sessions")
    
    def get_document_collection(self):
        return self.document_collection

    async def get_comprehensive_analytics(
        self, 
        user_id: str, 
        days: int = 30,
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive learning analytics with advanced insights
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            include_predictions: Whether to include prediction models
            
        Returns:
            Comprehensive analytics including performance, patterns, and predictions
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Gather all learning data concurrently
            learning_data = await asyncio.gather(
                self._get_flashcard_performance_data(user_id, start_date, end_date),
                self._get_quiz_performance_data(user_id, start_date, end_date),
                self._get_chat_interaction_data(user_id, start_date, end_date),
                self._get_document_engagement_data(user_id, start_date, end_date),
                return_exceptions=True
            )
            
            flashcard_data, quiz_data, chat_data, document_data = learning_data
            
            # Calculate comprehensive metrics
            learning_metrics = await self._calculate_learning_metrics(
                user_id, flashcard_data, quiz_data, chat_data, days
            )
            
            # Analyze performance patterns
            performance_analysis = await self._analyze_performance_patterns(
                user_id, flashcard_data, quiz_data, days
            )
            
            # Generate study optimization recommendations
            study_optimization = await self._generate_study_optimization(
                user_id, learning_metrics, performance_analysis
            )
            
            # Analyze learning style and patterns
            learning_style = await self._identify_learning_style(
                user_id, flashcard_data, quiz_data, chat_data
            )
            
            study_pattern = await self._identify_study_pattern(
                user_id, flashcard_data, quiz_data, days
            )
            
            # Calculate Bloom's taxonomy mastery
            bloom_mastery = await self._calculate_bloom_mastery(user_id, quiz_data)
            
            # Predict performance and generate forecasts
            predictions = {}
            if include_predictions:
                predictions = await self._generate_performance_predictions(
                    user_id, learning_metrics, performance_analysis
                )
            
            # Generate personalized recommendations
            recommendations = await self._generate_advanced_recommendations(
                user_id, learning_metrics, performance_analysis, study_optimization
            )
            
            return {
                "user_id": user_id,
                "analysis_period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "learning_metrics": asdict(learning_metrics),
                "performance_analysis": asdict(performance_analysis),
                "study_optimization": asdict(study_optimization),
                "learning_style": learning_style.value,
                "study_pattern": study_pattern.value,
                "bloom_mastery": bloom_mastery,
                "predictions": predictions,
                "recommendations": [asdict(rec) for rec in recommendations],
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive analytics: {e}")
            return {"error": str(e), "user_id": user_id}

    async def _get_flashcard_performance_data(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get detailed flashcard performance data"""
        try:
            # Get user's flashcards
            flashcards = []
            async for card in self.flashcard_collection.find({"user_id": user_id}):
                flashcards.append(card)
            
            if not flashcards:
                return {
                    "total_cards": 0,
                    "cards_reviewed": 0,
                    "average_accuracy": 0.0,
                    "retention_rates": {},
                    "difficulty_performance": {},
                    "timing_analysis": {},
                    "spaced_repetition_effectiveness": 0.0
                }
            
            # Calculate performance metrics
            total_cards = len(flashcards)
            cards_reviewed = len([c for c in flashcards if c.get("review_count", 0) > 0])
            
            # Calculate accuracy by difficulty
            difficulty_performance = {}
            for difficulty in self.DIFFICULTY_LEVELS:
                difficulty_cards = [c for c in flashcards if c.get("difficulty") == difficulty]
                if difficulty_cards:
                    accuracy = self._calculate_accuracy(difficulty_cards)
                    difficulty_performance[difficulty] = accuracy
                else:
                    difficulty_performance[difficulty] = 0.0
            
            # Analyze retention using spaced repetition data
            retention_analysis = await self.spaced_repetition.analyze_forgetting_curve(user_id)
            retention_rates = {
                curve.interval_days: curve.retention_rate 
                for curve in retention_analysis
            }
            
            # Calculate spaced repetition effectiveness
            sr_effectiveness = await self._calculate_spaced_repetition_effectiveness(user_id)
            
            # Timing analysis
            timing_analysis = await self._analyze_study_timing(user_id, flashcards, start_date, end_date)
            
            return {
                "total_cards": total_cards,
                "cards_reviewed": cards_reviewed,
                "average_accuracy": self._calculate_accuracy(flashcards),
                "retention_rates": retention_rates,
                "difficulty_performance": difficulty_performance,
                "timing_analysis": timing_analysis,
                "spaced_repetition_effectiveness": sr_effectiveness
            }
            
        except Exception as e:
            logger.error(f"Error getting flashcard performance data: {e}")
            return {}

    async def _get_quiz_performance_data(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get detailed quiz performance data"""
        try:
            # Get quiz attempts in period
            attempts = []
            async for attempt in self.quiz_collection.find({
                "user_id": user_id,
                "completed_at": {"$gte": start_date, "$lte": end_date}
            }):
                attempts.append(attempt)
            
            if not attempts:
                return {
                    "total_attempts": 0,
                    "average_score": 0.0,
                    "bloom_performance": {},
                    "difficulty_trends": {},
                    "improvement_rate": 0.0,
                    "consistency_score": 0.0,
                    "time_efficiency": 0.0
                }
            
            # Calculate performance metrics
            scores = [attempt.get("percentage", 0) for attempt in attempts]
            average_score = statistics.mean(scores) if scores else 0.0
            
            # Bloom's taxonomy performance
            bloom_performance = self._analyze_bloom_performance(attempts)
            
            # Calculate improvement rate using linear regression
            improvement_rate = self._calculate_improvement_rate(scores)
            
            # Analyze difficulty trends
            difficulty_trends = self._analyze_difficulty_trends(attempts)
            
            # Calculate consistency score
            consistency_score = self._calculate_quiz_consistency(attempts)
            
            # Calculate time efficiency
            time_efficiency = self._calculate_time_efficiency(attempts)
            
            return {
                "total_attempts": len(attempts),
                "average_score": average_score,
                "bloom_performance": bloom_performance,
                "difficulty_trends": difficulty_trends,
                "improvement_rate": improvement_rate,
                "consistency_score": consistency_score,
                "time_efficiency": time_efficiency,
                "score_distribution": self._calculate_score_distribution(scores)
            }
            
        except Exception as e:
            logger.error(f"Error getting quiz performance data: {e}")
            return {}

    async def _get_chat_interaction_data(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get detailed chat interaction data"""
        try:
            # Get chat messages in period
            messages = []
            async for message in self.chat_collection.find({
                "user_id": user_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }):
                messages.append(message)
            
            if not messages:
                return {
                    "total_interactions": 0,
                    "question_complexity": 0.0,
                    "topic_diversity": 0.0,
                    "engagement_patterns": {},
                    "learning_intent": "unknown"
                }
            
            # Analyze question complexity
            question_complexity = self._analyze_question_complexity(messages)
            
            # Calculate topic diversity
            topic_diversity = self._analyze_topic_diversity(messages)
            
            # Analyze engagement patterns
            engagement_patterns = self._analyze_engagement_patterns(messages)
            
            # Identify learning intent
            learning_intent = self._identify_learning_intent(messages)
            
            return {
                "total_interactions": len(messages),
                "question_complexity": question_complexity,
                "topic_diversity": topic_diversity,
                "engagement_patterns": engagement_patterns,
                "learning_intent": learning_intent
            }
            
        except Exception as e:
            logger.error(f"Error getting chat interaction data: {e}")
            return {}

    async def _get_document_engagement_data(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get document engagement data"""
        try:
            # Get documents user has interacted with
            engaged_docs = set()
            
            # From flashcards
            async for card in self.flashcard_collection.find({"user_id": user_id}):
                if card.get("document_id"):
                    engaged_docs.add(card["document_id"])
            
            # From quizzes
            async for attempt in self.quiz_collection.find({"user_id": user_id}):
                quiz_collection = mongodb_manager.get_collection("quizzes")
                quiz = await quiz_collection.find_one({"quiz_id": attempt.get("quiz_id")})
                if quiz and quiz.get("document_id"):
                    engaged_docs.add(quiz["document_id"])
            
            # From chat
            async for chat in self.chat_collection.find({"user_id": user_id}):
                if chat.get("document_id"):
                    engaged_docs.add(chat["document_id"])
            
            # Calculate engagement depth per document
            document_engagement = {}
            for doc_id in engaged_docs:
                engagement_score = await self._calculate_document_engagement_score(user_id, doc_id)
                document_engagement[doc_id] = engagement_score
            
            return {
                "total_documents": len(engaged_docs),
                "document_engagement": document_engagement,
                "average_engagement": statistics.mean(document_engagement.values()) if document_engagement else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting document engagement data: {e}")
            return {}

    # Helper methods for advanced analytics calculations
    
    def _calculate_accuracy(self, cards: List[Dict[str, Any]]) -> float:
        """Calculate accuracy rate for a set of cards"""
        if not cards:
            return 0.0
        
        total_correct = sum(card.get("correct_count", 0) for card in cards)
        total_reviews = sum(card.get("review_count", 0) for card in cards)
        
        return total_correct / total_reviews if total_reviews > 0 else 0.0
    
    async def _calculate_spaced_repetition_effectiveness(self, user_id: str) -> float:
        """Calculate effectiveness of spaced repetition algorithm"""
        try:
            # Get learning statistics from spaced repetition service
            stats = await self.spaced_repetition.get_learning_statistics(user_id)
            
            # Calculate effectiveness based on multiple factors
            retention_factor = stats.retention_rate
            velocity_factor = min(1.0, stats.learning_velocity / 2.0)  # Normalize to max 2 cards/day
            consistency_factor = stats.consistency_score
            
            effectiveness = (
                retention_factor * 0.5 + 
                velocity_factor * 0.3 + 
                consistency_factor * 0.2
            )
            
            return min(1.0, effectiveness)
            
        except Exception as e:
            logger.error(f"Error calculating spaced repetition effectiveness: {e}")
            return 0.5
    
    async def _analyze_study_timing(
        self, 
        user_id: str, 
        flashcards: List[Dict[str, Any]], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze study timing patterns"""
        try:
            # Analyze when user studies most effectively
            study_times = []
            
            # Get timestamps from card updates (proxy for study sessions)
            for card in flashcards:
                updated_at = card.get("updated_at")
                if updated_at and start_date <= updated_at <= end_date:
                    study_times.append(updated_at)
            
            if not study_times:
                return {
                    "peak_hours": [],
                    "peak_days": [],
                    "consistency": 0.0,
                    "optimal_session_length": 30
                }
            
            # Analyze peak hours
            hour_counts = Counter(time.hour for time in study_times)
            peak_hours = [hour for hour, count in hour_counts.most_common(3)]
            
            # Analyze peak days
            day_counts = Counter(time.strftime("%A") for time in study_times)
            peak_days = [day for day, count in day_counts.most_common(3)]
            
            # Calculate consistency
            unique_days = len(set(time.date() for time in study_times))
            total_days = (end_date - start_date).days
            consistency = unique_days / total_days if total_days > 0 else 0.0
            
            return {
                "peak_hours": peak_hours,
                "peak_days": peak_days,
                "consistency": consistency,
                "optimal_session_length": 30  # Could be calculated from session data
            }
            
        except Exception as e:
            logger.error(f"Error analyzing study timing: {e}")
            return {}
    
    def _analyze_bloom_performance(self, attempts: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze performance across Bloom's taxonomy levels"""
        bloom_scores = defaultdict(list)
        
        for attempt in attempts:
            bloom_data = attempt.get("bloom_scores", {})
            for level, score in bloom_data.items():
                bloom_scores[level].append(score)
        
        bloom_performance = {}
        for level in self.BLOOM_LEVELS:
            if level in bloom_scores and bloom_scores[level]:
                bloom_performance[level] = statistics.mean(bloom_scores[level])
            else:
                bloom_performance[level] = 0.0
        
        return bloom_performance
    
    def _calculate_improvement_rate(self, scores: List[float]) -> float:
        """Calculate improvement rate using linear regression"""
        if len(scores) < 2:
            return 0.0
        
        try:
            # Simple linear regression
            n = len(scores)
            x_values = list(range(n))
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(scores)
            
            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, scores))
            denominator = sum((x - x_mean) ** 2 for x in x_values)
            
            slope = numerator / denominator if denominator != 0 else 0
            return slope
            
        except Exception:
            return 0.0
    
    def _analyze_difficulty_trends(self, attempts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends across difficulty levels"""
        # This would analyze how performance changes with question difficulty
        # For now, return basic analysis
        return {
            "easy_trend": "stable",
            "medium_trend": "improving", 
            "hard_trend": "stable"
        }
    
    def _calculate_quiz_consistency(self, attempts: List[Dict[str, Any]]) -> float:
        """Calculate consistency score for quiz performance"""
        if len(attempts) < 2:
            return 0.0
        
        scores = [attempt.get("percentage", 0) for attempt in attempts]
        mean_score = statistics.mean(scores)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
        
        # Lower standard deviation = higher consistency
        consistency = max(0.0, 1.0 - (std_dev / 100.0))
        return consistency
    
    def _calculate_time_efficiency(self, attempts: List[Dict[str, Any]]) -> float:
        """Calculate time efficiency for quiz attempts"""
        if not attempts:
            return 0.0
        
        # Calculate average time per question
        time_per_question = []
        for attempt in attempts:
            time_taken = attempt.get("time_taken", 0)
            questions = len(attempt.get("question_results", []))
            if questions > 0 and time_taken > 0:
                time_per_question.append(time_taken / questions)
        
        if not time_per_question:
            return 0.5
        
        avg_time = statistics.mean(time_per_question)
        # Normalize efficiency (assume 60 seconds per question is baseline)
        efficiency = min(1.0, 60.0 / avg_time) if avg_time > 0 else 0.5
        return efficiency
    
    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution across grade ranges"""
        if not scores:
            return {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for score in scores:
            if score >= 90:
                distribution["A"] += 1
            elif score >= 80:
                distribution["B"] += 1
            elif score >= 70:
                distribution["C"] += 1
            elif score >= 60:
                distribution["D"] += 1
            else:
                distribution["F"] += 1
        
        return distribution
    
    def _analyze_question_complexity(self, messages: List[Dict[str, Any]]) -> float:
        """Analyze complexity of chat questions"""
        if not messages:
            return 0.0
        
        total_complexity = 0
        for message in messages:
            question = message.get("question", "")
            # Simple complexity analysis based on length and question words
            complexity = min(1.0, len(question.split()) / 20.0)  # Normalize to max 20 words
            
            # Bonus for question words
            question_words = ["what", "how", "why", "when", "where", "which", "who"]
            if any(word in question.lower() for word in question_words):
                complexity += 0.2
            
            total_complexity += min(1.0, complexity)
        
        return total_complexity / len(messages)
    
    def _analyze_topic_diversity(self, messages: List[Dict[str, Any]]) -> float:
        """Analyze diversity of topics in chat interactions"""
        if not messages:
            return 0.0
        
        # Simple topic analysis using unique words
        all_words = set()
        for message in messages:
            question = message.get("question", "").lower()
            words = [word for word in question.split() if len(word) > 3]
            all_words.update(words)
        
        # Normalize diversity score
        diversity = min(1.0, len(all_words) / (len(messages) * 5))  # Max 5 unique words per message
        return diversity
    
    def _analyze_engagement_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze engagement patterns in chat interactions"""
        if not messages:
            return {"frequency": "low", "depth": "shallow", "progression": "none"}
        
        # Analyze frequency
        time_spans = []
        sorted_messages = sorted(messages, key=lambda x: x.get("created_at", datetime.min))
        
        for i in range(1, len(sorted_messages)):
            time_diff = (sorted_messages[i]["created_at"] - sorted_messages[i-1]["created_at"]).total_seconds()
            time_spans.append(time_diff)
        
        avg_gap = statistics.mean(time_spans) if time_spans else 86400  # Default 1 day
        
        if avg_gap < 3600:  # Less than 1 hour
            frequency = "high"
        elif avg_gap < 86400:  # Less than 1 day
            frequency = "medium"
        else:
            frequency = "low"
        
        # Analyze depth (based on question length)
        avg_length = statistics.mean([len(msg.get("question", "")) for msg in messages])
        if avg_length > 100:
            depth = "deep"
        elif avg_length > 50:
            depth = "medium"
        else:
            depth = "shallow"
        
        return {
            "frequency": frequency,
            "depth": depth,
            "progression": "improving"  # Could be calculated from complexity trends
        }
    
    def _identify_learning_intent(self, messages: List[Dict[str, Any]]) -> str:
        """Identify primary learning intent from chat patterns"""
        if not messages:
            return "unknown"
        
        # Simple intent classification based on question patterns
        clarification_words = ["what", "define", "explain", "clarify"]
        application_words = ["how", "use", "apply", "implement"] 
        analysis_words = ["why", "compare", "analyze", "evaluate"]
        
        clarification_count = 0
        application_count = 0
        analysis_count = 0
        
        for message in messages:
            question = message.get("question", "").lower()
            
            if any(word in question for word in clarification_words):
                clarification_count += 1
            elif any(word in question for word in application_words):
                application_count += 1
            elif any(word in question for word in analysis_words):
                analysis_count += 1
        
        max_count = max(clarification_count, application_count, analysis_count)
        
        if max_count == clarification_count:
            return "clarification"
        elif max_count == application_count:
            return "application"
        elif max_count == analysis_count:
            return "analysis"
        else:
            return "exploration"
    
    async def _calculate_document_engagement_score(self, user_id: str, document_id: str) -> float:
        """Calculate engagement score for a specific document"""
        try:
            engagement_score = 0.0
            
            # Count flashcards from this document
            flashcard_count = await self.flashcard_collection.count_documents({
                "user_id": user_id,
                "document_id": document_id
            })
            engagement_score += flashcard_count * 0.3
            
            # Count quiz attempts
            quiz_collection = mongodb_manager.get_collection("quizzes")
            quizzes = []
            async for quiz in quiz_collection.find({"document_id": document_id}):
                quizzes.append(quiz["quiz_id"])
            
            quiz_attempts = 0
            if quizzes:
                quiz_attempts = await self.quiz_collection.count_documents({
                    "user_id": user_id,
                    "quiz_id": {"$in": quizzes}
                })
            engagement_score += quiz_attempts * 0.4
            
            # Count chat interactions
            chat_count = await self.chat_collection.count_documents({
                "user_id": user_id,
                "document_id": document_id
            })
            engagement_score += chat_count * 0.3
            
            # Normalize to 0-1 scale
            return min(1.0, engagement_score / 10.0)
            
        except Exception as e:
            logger.error(f"Error calculating document engagement: {e}")
            return 0.0

    # Advanced analytics calculation methods
    
    async def _calculate_learning_metrics(
        self, 
        user_id: str,
        flashcard_data: Dict[str, Any],
        quiz_data: Dict[str, Any], 
        chat_data: Dict[str, Any],
        days: int
    ) -> LearningMetrics:
        """Calculate comprehensive learning metrics"""
        try:
            # Retention rate from flashcards and quizzes
            flashcard_retention = flashcard_data.get("spaced_repetition_effectiveness", 0.5)
            quiz_retention = quiz_data.get("average_score", 0) / 100.0
            retention_rate = (flashcard_retention + quiz_retention) / 2.0
            
            # Learning velocity (progress per day)
            cards_reviewed = flashcard_data.get("cards_reviewed", 0)
            quizzes_taken = quiz_data.get("total_attempts", 0)
            learning_velocity = (cards_reviewed + quizzes_taken * 5) / days  # Weight quizzes more
            
            # Consistency score
            timing_analysis = flashcard_data.get("timing_analysis", {})
            quiz_consistency = quiz_data.get("consistency_score", 0.5)
            consistency_score = (timing_analysis.get("consistency", 0.5) + quiz_consistency) / 2.0
            
            # Difficulty mastery
            difficulty_mastery = flashcard_data.get("difficulty_performance", {})
            
            # Bloom's mastery
            bloom_mastery = quiz_data.get("bloom_performance", {})
            
            # Optimal study time (based on timing analysis)
            peak_hours = timing_analysis.get("peak_hours", [])
            optimal_study_time = peak_hours[0] if peak_hours else 14  # Default 2 PM
            
            # Predicted performance
            improvement_rate = quiz_data.get("improvement_rate", 0)
            current_performance = quiz_data.get("average_score", 70) / 100.0
            predicted_performance = min(1.0, current_performance + improvement_rate * 0.1)
            
            # Learning efficiency
            time_efficiency = quiz_data.get("time_efficiency", 0.5)
            accuracy = flashcard_data.get("average_accuracy", 0.7)
            learning_efficiency = (time_efficiency + accuracy) / 2.0
            
            # Knowledge retention curve
            retention_rates = flashcard_data.get("retention_rates", {})
            knowledge_retention_curve = [(interval, rate) for interval, rate in retention_rates.items()]
            
            return LearningMetrics(
                retention_rate=retention_rate,
                learning_velocity=learning_velocity,
                consistency_score=consistency_score,
                difficulty_mastery=difficulty_mastery,
                bloom_mastery=bloom_mastery,
                optimal_study_time=optimal_study_time,
                predicted_performance=predicted_performance,
                learning_efficiency=learning_efficiency,
                knowledge_retention_curve=knowledge_retention_curve
            )
            
        except Exception as e:
            logger.error(f"Error calculating learning metrics: {e}")
            return LearningMetrics(
                retention_rate=0.5, learning_velocity=0.0, consistency_score=0.5,
                difficulty_mastery={}, bloom_mastery={}, optimal_study_time=14,
                predicted_performance=0.7, learning_efficiency=0.5, knowledge_retention_curve=[]
            )
    
    async def _analyze_performance_patterns(
        self,
        user_id: str,
        flashcard_data: Dict[str, Any],
        quiz_data: Dict[str, Any],
        days: int
    ) -> PerformanceAnalysis:
        """Analyze performance patterns and identify strengths/weaknesses"""
        try:
            # Identify strengths
            strengths = []
            bloom_performance = quiz_data.get("bloom_performance", {})
            difficulty_performance = flashcard_data.get("difficulty_performance", {})
            
            # Find strongest Bloom's levels
            for level, score in bloom_performance.items():
                if score > 80:
                    strengths.append(f"Bloom's {level} (คะแนน {score:.1f}%)")
            
            # Find strongest difficulty levels
            for difficulty, score in difficulty_performance.items():
                if score > 0.8:
                    strengths.append(f"ความยาก {difficulty} (ความแม่นยำ {score:.1%})")
            
            # Identify weaknesses
            weaknesses = []
            for level, score in bloom_performance.items():
                if score < 60:
                    weaknesses.append(f"Bloom's {level} (คะแนน {score:.1f}%)")
            
            for difficulty, score in difficulty_performance.items():
                if score < 0.6:
                    weaknesses.append(f"ความยาก {difficulty} (ความแม่นยำ {score:.1%})")
            
            # Improvement areas
            improvement_areas = []
            if quiz_data.get("consistency_score", 0.5) < 0.6:
                improvement_areas.append("ความสม่ำเสมอในการทำแบบทดสอบ")
            
            if flashcard_data.get("spaced_repetition_effectiveness", 0.5) < 0.7:
                improvement_areas.append("ประสิทธิภาพการทบทวนแบบเว้นระยะ")
            
            if quiz_data.get("time_efficiency", 0.5) < 0.6:
                improvement_areas.append("ความเร็วในการตอบคำถาม")
            
            # Mastery timeline estimation
            mastery_timeline = {}
            for level, score in bloom_performance.items():
                if score < 80:
                    days_to_mastery = max(7, int((80 - score) / 2))  # Estimate 2% improvement per day
                    mastery_timeline[level] = days_to_mastery
            
            # Confidence intervals (simplified)
            confidence_intervals = {}
            for level, score in bloom_performance.items():
                margin = 5.0  # ±5% confidence interval
                confidence_intervals[level] = (max(0, score - margin), min(100, score + margin))
            
            # Trend analysis
            trend_analysis = {}
            improvement_rate = quiz_data.get("improvement_rate", 0)
            if improvement_rate > 1:
                trend_analysis["overall"] = "improving"
            elif improvement_rate < -1:
                trend_analysis["overall"] = "declining"
            else:
                trend_analysis["overall"] = "stable"
            
            return PerformanceAnalysis(
                strengths=strengths,
                weaknesses=weaknesses,
                improvement_areas=improvement_areas,
                mastery_timeline=mastery_timeline,
                confidence_intervals=confidence_intervals,
                trend_analysis=trend_analysis
            )
            
        except Exception as e:
            logger.error(f"Error analyzing performance patterns: {e}")
            return PerformanceAnalysis(
                strengths=[], weaknesses=[], improvement_areas=[],
                mastery_timeline={}, confidence_intervals={}, trend_analysis={}
            )
    
    async def _generate_study_optimization(
        self,
        user_id: str,
        learning_metrics: LearningMetrics,
        performance_analysis: PerformanceAnalysis
    ) -> StudyOptimization:
        """Generate study optimization recommendations"""
        try:
            # Optimal session length based on efficiency
            if learning_metrics.learning_efficiency > 0.8:
                optimal_session_length = 45  # Can handle longer sessions
            elif learning_metrics.learning_efficiency > 0.6:
                optimal_session_length = 30  # Standard session
            else:
                optimal_session_length = 20  # Shorter sessions for lower efficiency
            
            # Best study times
            best_study_times = [f"{learning_metrics.optimal_study_time:02d}:00"]
            if learning_metrics.consistency_score > 0.7:
                # Add secondary time slots for consistent learners
                secondary_time = (learning_metrics.optimal_study_time + 6) % 24
                best_study_times.append(f"{secondary_time:02d}:00")
            
            # Break frequency
            if learning_metrics.learning_efficiency < 0.6:
                recommended_break_frequency = 15  # More frequent breaks
            else:
                recommended_break_frequency = 25  # Standard pomodoro
            
            # Difficulty progression
            easy_mastery = learning_metrics.difficulty_mastery.get("easy", 0.7)
            medium_mastery = learning_metrics.difficulty_mastery.get("medium", 0.6)
            hard_mastery = learning_metrics.difficulty_mastery.get("hard", 0.5)
            
            if easy_mastery > 0.8 and medium_mastery > 0.7:
                difficulty_progression = "เน้นระดับยาก"
            elif easy_mastery > 0.7:
                difficulty_progression = "เน้นระดับปานกลาง"
            else:
                difficulty_progression = "เน้นระดับง่าย"
            
            # Content prioritization
            content_prioritization = []
            for weakness in performance_analysis.weaknesses[:3]:  # Top 3 weaknesses
                content_prioritization.append(f"ทบทวน {weakness}")
            
            # Spaced repetition schedule
            retention_rate = learning_metrics.retention_rate
            if retention_rate < 0.7:
                schedule_intensity = "intensive"
                review_frequency = "daily"
            elif retention_rate < 0.85:
                schedule_intensity = "standard"
                review_frequency = "every_2_days"
            else:
                schedule_intensity = "maintenance"
                review_frequency = "every_3_days"
            
            spaced_repetition_schedule = {
                "intensity": schedule_intensity,
                "review_frequency": review_frequency,
                "new_cards_per_day": max(5, int(learning_metrics.learning_velocity)),
                "max_reviews_per_day": min(50, int(learning_metrics.learning_velocity * 10))
            }
            
            return StudyOptimization(
                optimal_session_length=optimal_session_length,
                best_study_times=best_study_times,
                recommended_break_frequency=recommended_break_frequency,
                difficulty_progression=difficulty_progression,
                content_prioritization=content_prioritization,
                spaced_repetition_schedule=spaced_repetition_schedule
            )
            
        except Exception as e:
            logger.error(f"Error generating study optimization: {e}")
            return StudyOptimization(
                optimal_session_length=30, best_study_times=["14:00"],
                recommended_break_frequency=25, difficulty_progression="เน้นระดับปานกลาง",
                content_prioritization=[], spaced_repetition_schedule={}
            )
    
    async def _identify_learning_style(
        self,
        user_id: str,
        flashcard_data: Dict[str, Any],
        quiz_data: Dict[str, Any],
        chat_data: Dict[str, Any]
    ) -> LearningStyle:
        """Identify user's learning style based on activity patterns"""
        try:
            # Analyze activity preferences
            flashcard_usage = flashcard_data.get("cards_reviewed", 0)
            quiz_usage = quiz_data.get("total_attempts", 0)
            chat_usage = chat_data.get("total_interactions", 0)
            
            # Calculate preference scores
            visual_score = flashcard_usage * 0.6 + quiz_usage * 0.4  # Visual materials
            reading_writing_score = chat_usage * 0.8 + quiz_usage * 0.3  # Text-based
            kinesthetic_score = quiz_usage * 0.5 + flashcard_usage * 0.3  # Interactive
            
            # Normalize scores
            total_score = visual_score + reading_writing_score + kinesthetic_score
            if total_score == 0:
                return LearningStyle.MIXED
            
            visual_ratio = visual_score / total_score
            reading_ratio = reading_writing_score / total_score
            kinesthetic_ratio = kinesthetic_score / total_score
            
            # Determine dominant style
            max_ratio = max(visual_ratio, reading_ratio, kinesthetic_ratio)
            
            if max_ratio < 0.4:  # No clear preference
                return LearningStyle.MIXED
            elif visual_ratio == max_ratio:
                return LearningStyle.VISUAL
            elif reading_ratio == max_ratio:
                return LearningStyle.READING_WRITING
            else:
                return LearningStyle.KINESTHETIC
                
        except Exception as e:
            logger.error(f"Error identifying learning style: {e}")
            return LearningStyle.MIXED
    
    async def _identify_study_pattern(
        self,
        user_id: str,
        flashcard_data: Dict[str, Any],
        quiz_data: Dict[str, Any],
        days: int
    ) -> StudyPattern:
        """Identify user's study pattern"""
        try:
            consistency_score = flashcard_data.get("timing_analysis", {}).get("consistency", 0.5)
            quiz_consistency = quiz_data.get("consistency_score", 0.5)
            overall_consistency = (consistency_score + quiz_consistency) / 2.0
            
            total_activities = flashcard_data.get("cards_reviewed", 0) + quiz_data.get("total_attempts", 0)
            daily_average = total_activities / days if days > 0 else 0
            
            # Classify pattern
            if overall_consistency > 0.8 and daily_average > 5:
                return StudyPattern.CONSISTENT
            elif overall_consistency > 0.6:
                return StudyPattern.BALANCED
            elif daily_average > 10:
                return StudyPattern.INTENSIVE
            elif overall_consistency < 0.3:
                return StudyPattern.SPORADIC
            else:
                return StudyPattern.CRAMMING
                
        except Exception as e:
            logger.error(f"Error identifying study pattern: {e}")
            return StudyPattern.BALANCED
    
    async def _calculate_bloom_mastery(self, user_id: str, quiz_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate detailed Bloom's taxonomy mastery"""
        try:
            bloom_performance = quiz_data.get("bloom_performance", {})
            
            # Enhanced mastery calculation with confidence weighting
            mastery_scores = {}
            for level in self.BLOOM_LEVELS:
                raw_score = bloom_performance.get(level, 0.0)
                
                # Apply confidence weighting based on number of attempts
                # This would ideally use actual attempt counts per level
                confidence_weight = 0.8  # Simplified
                
                mastery_score = raw_score * confidence_weight
                mastery_scores[level] = mastery_score
            
            return mastery_scores
            
        except Exception as e:
            logger.error(f"Error calculating Bloom's mastery: {e}")
            return {level: 0.0 for level in self.BLOOM_LEVELS}
    
    async def _generate_performance_predictions(
        self,
        user_id: str,
        learning_metrics: LearningMetrics,
        performance_analysis: PerformanceAnalysis
    ) -> Dict[str, Any]:
        """Generate performance predictions using trends and patterns"""
        try:
            # Predict future performance
            current_performance = learning_metrics.predicted_performance
            improvement_trend = 0.02 if learning_metrics.learning_velocity > 1 else 0.01
            
            # 7-day prediction
            week_prediction = min(1.0, current_performance + improvement_trend * 7)
            
            # 30-day prediction
            month_prediction = min(1.0, current_performance + improvement_trend * 30)
            
            # Mastery timeline predictions
            mastery_predictions = {}
            for topic, days_to_mastery in performance_analysis.mastery_timeline.items():
                mastery_predictions[topic] = {
                    "current_level": learning_metrics.bloom_mastery.get(topic, 0.0),
                    "predicted_mastery_date": (datetime.utcnow() + timedelta(days=days_to_mastery)).isoformat(),
                    "confidence": 0.8 if learning_metrics.consistency_score > 0.7 else 0.6
                }
            
            return {
                "short_term": {
                    "7_day_performance": week_prediction * 100,
                    "confidence": 0.85
                },
                "long_term": {
                    "30_day_performance": month_prediction * 100,
                    "confidence": 0.70
                },
                "mastery_timeline": mastery_predictions,
                "risk_factors": performance_analysis.improvement_areas[:3]
            }
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {}
    
    async def _generate_advanced_recommendations(
        self,
        user_id: str,
        learning_metrics: LearningMetrics,
        performance_analysis: PerformanceAnalysis,
        study_optimization: StudyOptimization
    ) -> List[StudyRecommendation]:
        """Generate advanced personalized recommendations"""
        try:
            recommendations = []
            
            # Performance-based recommendations
            if learning_metrics.retention_rate < 0.7:
                recommendations.append(StudyRecommendation(
                    type="retention_improvement",
                    title="เพิ่มประสิทธิภาพการจำ",
                    description=f"อัตราการจำปัจจุบัน {learning_metrics.retention_rate:.1%} ควรปรับปรุง",
                    priority="high"
                ))
            
            # Consistency recommendations
            if learning_metrics.consistency_score < 0.6:
                recommendations.append(StudyRecommendation(
                    type="consistency_improvement",
                    title="เพิ่มความสม่ำเสมอ",
                    description=f"เรียนให้สม่ำเสมอในช่วงเวลา {', '.join(study_optimization.best_study_times)}",
                    priority="high"
                ))
            
            # Bloom's taxonomy recommendations
            for weakness in performance_analysis.weaknesses[:2]:
                recommendations.append(StudyRecommendation(
                    type="skill_development",
                    title=f"พัฒนาทักษะ {weakness}",
                    description="ฝึกฝนเพิ่มเติมในพื้นที่ที่อ่อน",
                    priority="medium"
                ))
            
            # Study optimization recommendations
            if study_optimization.optimal_session_length != 30:
                recommendations.append(StudyRecommendation(
                    type="session_optimization",
                    title=f"ปรับระยะเวลาการเรียน",
                    description=f"เรียนครั้งละ {study_optimization.optimal_session_length} นาทีจะมีประสิทธิภาพที่สุด",
                    priority="medium"
                ))
            
            # Positive reinforcement
            if learning_metrics.learning_efficiency > 0.8:
                recommendations.append(StudyRecommendation(
                    type="achievement",
                    title="ผลงานดีเยี่ยม!",
                    description="ประสิทธิภาพการเรียนรู้ของคุณอยู่ในระดับสูง",
                    priority="low"
                ))
            
            return recommendations[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    async def track_learning_session(
        self,
        user_id: str,
        activity_type: str,
        document_id: str,
        duration: int,
        details: Dict[str, Any]
    ) -> str:
        """Track a learning session"""
        try:
            session = LearningSession(
                user_id=user_id,
                activity_type=activity_type,
                document_id=document_id,
                duration=duration,
                details=details
            )
            
            collection = self.get_session_collection()
            result = await collection.insert_one(session.dict(by_alias=True))
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error tracking learning session: {e}")
            return ""

    async def get_user_analytics(self, user_id: str, days: int = 30) -> UserAnalytics:
        """Get comprehensive analytics for a user"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get flashcard stats
            flashcard_stats = await self._get_flashcard_analytics(user_id, start_date, end_date)
            
            # Get quiz stats
            quiz_stats = await self._get_quiz_analytics(user_id, start_date, end_date)
            
            # Get chat stats
            chat_stats = await self._get_chat_analytics(user_id, start_date, end_date)
            
            # Get study patterns
            study_patterns = await self._get_study_patterns(user_id, start_date, end_date)
            
            # Get learning progress
            learning_progress = await self._calculate_learning_progress(user_id, start_date, end_date)
            
            # Get recommendations
            recommendations = await self._generate_study_recommendations(user_id)
            
            return UserAnalytics(
                user_id=user_id,
                period_days=days,
                flashcard_stats=flashcard_stats,
                quiz_stats=quiz_stats,
                chat_stats=chat_stats,
                study_patterns=study_patterns,
                learning_progress=learning_progress,
                recommendations=recommendations,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return UserAnalytics(user_id=user_id, period_days=days)

    async def _get_flashcard_analytics(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get flashcard analytics for user"""
        try:
            # Get flashcard reviews in period
            flashcard_collection = mongodb_manager.get_collection("flashcard_reviews")
            reviews = []
            
            async for review in flashcard_collection.find({
                "user_id": user_id,
                "reviewed_at": {"$gte": start_date, "$lte": end_date}
            }):
                reviews.append(review)
            
            if not reviews:
                return {
                    "total_reviews": 0,
                    "average_quality": 0,
                    "retention_rate": 0,
                    "streak_days": 0,
                    "cards_mastered": 0
                }
            
            # Calculate metrics
            total_reviews = len(reviews)
            average_quality = sum(r.get("quality", 0) for r in reviews) / total_reviews
            
            # Calculate retention rate (quality >= 3)
            good_reviews = sum(1 for r in reviews if r.get("quality", 0) >= 3)
            retention_rate = (good_reviews / total_reviews) * 100 if total_reviews > 0 else 0
            
            # Calculate streak
            streak_days = await self._calculate_study_streak(user_id)
            
            # Count mastered cards (quality 5 in last review)
            mastered_cards = 0
            card_last_quality = {}
            
            for review in sorted(reviews, key=lambda x: x.get("reviewed_at", datetime.min)):
                card_id = review.get("card_id")
                if card_id:
                    card_last_quality[card_id] = review.get("quality", 0)
            
            mastered_cards = sum(1 for quality in card_last_quality.values() if quality >= 5)
            
            return {
                "total_reviews": total_reviews,
                "average_quality": round(average_quality, 2),
                "retention_rate": round(retention_rate, 2),
                "streak_days": streak_days,
                "cards_mastered": mastered_cards
            }
            
        except Exception as e:
            logger.error(f"Error getting flashcard analytics: {e}")
            return {"total_reviews": 0, "average_quality": 0, "retention_rate": 0, "streak_days": 0, "cards_mastered": 0}

    async def _get_quiz_analytics(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get quiz analytics for user"""
        try:
            # Get quiz attempts in period
            quiz_collection = self.get_quiz_collection()
            attempts = []
            async for attempt in quiz_collection.find({
                "user_id": user_id,
                "completed_at": {"$gte": start_date, "$lte": end_date}
            }):
                attempts.append(attempt)
            
            if not attempts:
                return {
                    "total_attempts": 0,
                    "average_score": 0,
                    "improvement_rate": 0,
                    "bloom_strengths": [],
                    "bloom_weaknesses": [],
                    "bloom_averages": {}
                }
            
            # Calculate metrics
            total_attempts = len(attempts)
            scores = [attempt.get("percentage", 0) for attempt in attempts]
            average_score = sum(scores) / len(scores) if scores else 0
            
            # Calculate improvement rate
            improvement_rate = 0
            if len(scores) > 1:
                first_half = scores[:len(scores)//2]
                second_half = scores[len(scores)//2:]
                if first_half and second_half:
                    improvement_rate = (sum(second_half)/len(second_half)) - (sum(first_half)/len(first_half))
            
            # Analyze Bloom's taxonomy performance
            bloom_scores = defaultdict(list)
            for attempt in attempts:
                for level, score in attempt.get("bloom_scores", {}).items():
                    bloom_scores[level].append(score)
            
            bloom_averages = {level: sum(scores)/len(scores) for level, scores in bloom_scores.items() if scores}
            
            # Identify strengths and weaknesses
            sorted_bloom = sorted(bloom_averages.items(), key=lambda x: x[1], reverse=True)
            bloom_strengths = [level for level, score in sorted_bloom[:2] if score >= 70]
            bloom_weaknesses = [level for level, score in sorted_bloom[-2:] if score < 70]
            
            return {
                "total_attempts": total_attempts,
                "average_score": round(average_score, 2),
                "improvement_rate": round(improvement_rate, 2),
                "bloom_strengths": bloom_strengths,
                "bloom_weaknesses": bloom_weaknesses,
                "bloom_averages": bloom_averages
            }
            
        except Exception as e:
            logger.error(f"Error getting quiz analytics: {e}")
            return {"total_attempts": 0, "average_score": 0, "improvement_rate": 0, "bloom_strengths": [], "bloom_weaknesses": [], "bloom_averages": {}}

    async def _get_chat_analytics(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get chat analytics for user"""
        try:
            # Get chat messages in period
            chat_collection = self.get_chat_collection()
            messages = []
            async for message in chat_collection.find({
                "user_id": user_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }):
                messages.append(message)
            
            if not messages:
                return {
                    "total_questions": 0,
                    "average_confidence": 0,
                    "topics_explored": 0,
                    "engagement_level": "low"
                }
            
            # Calculate metrics
            total_questions = len(messages)
            confidences = [msg.get("confidence", 0) for msg in messages]
            average_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Count unique topics (simple keyword analysis)
            topics = set()
            for message in messages:
                question = message.get("question", "").lower()
                # Simple topic extraction (in production, use more sophisticated NLP)
                words = question.split()
                for word in words:
                    if len(word) > 3:
                        topics.add(word)
            
            topics_explored = len(topics)
            
            # Determine engagement level
            engagement_level = "low"
            if total_questions > 20:
                engagement_level = "high"
            elif total_questions > 10:
                engagement_level = "medium"
            
            return {
                "total_questions": total_questions,
                "average_confidence": round(average_confidence, 2),
                "topics_explored": topics_explored,
                "engagement_level": engagement_level
            }
            
        except Exception as e:
            logger.error(f"Error getting chat analytics: {e}")
            return {"total_questions": 0, "average_confidence": 0, "topics_explored": 0, "engagement_level": "low"}

    async def _get_study_patterns(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze study patterns"""
        try:
            # Get all learning activities
            activities = []
            
            # Flashcard reviews
            flashcard_collection = mongodb_manager.get_collection("flashcard_reviews")
            async for review in flashcard_collection.find({
                "user_id": user_id,
                "reviewed_at": {"$gte": start_date, "$lte": end_date}
            }):
                activities.append({
                    "type": "flashcard",
                    "timestamp": review.get("reviewed_at"),
                    "duration": review.get("time_taken", 30)  # Default 30 seconds
                })
            
            # Quiz attempts
            quiz_collection = self.get_quiz_collection()
            async for attempt in quiz_collection.find({
                "user_id": user_id,
                "completed_at": {"$gte": start_date, "$lte": end_date}
            }):
                activities.append({
                    "type": "quiz",
                    "timestamp": attempt.get("completed_at"),
                    "duration": attempt.get("time_taken", 600)  # seconds
                })
            
            # Chat sessions
            chat_collection = self.get_chat_collection()
            async for chat in chat_collection.find({
                "user_id": user_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }):
                activities.append({
                    "type": "chat",
                    "timestamp": chat.get("created_at"),
                    "duration": 120  # Estimated 2 minutes per question
                })
            
            if not activities:
                return {
                    "total_study_time": 0,
                    "average_session_length": 0,
                    "most_active_day": "unknown",
                    "most_active_hour": 0,
                    "consistency_score": 0
                }
            
            # Calculate total study time (minutes)
            total_study_time = sum(activity["duration"] for activity in activities) / 60
            
            # Calculate average session length
            sessions = self._group_activities_into_sessions(activities)
            average_session_length = sum(s["duration"] for s in sessions) / len(sessions) if sessions else 0
            
            # Find most active day and hour
            day_counts = Counter()
            hour_counts = Counter()
            
            for activity in activities:
                timestamp = activity["timestamp"]
                if timestamp:
                    day_counts[timestamp.strftime("%A")] += 1
                    hour_counts[timestamp.hour] += 1
            
            most_active_day = day_counts.most_common(1)[0][0] if day_counts else "unknown"
            most_active_hour = hour_counts.most_common(1)[0][0] if hour_counts else 0
            
            # Calculate consistency score (0-100)
            # Based on how many days user studied out of total days
            study_days = set()
            for activity in activities:
                if activity["timestamp"]:
                    study_days.add(activity["timestamp"].date())
            
            total_days = (end_date - start_date).days
            consistency_score = (len(study_days) / total_days) * 100 if total_days > 0 else 0
            
            return {
                "total_study_time": round(total_study_time, 1),
                "average_session_length": round(average_session_length / 60, 1),  # minutes
                "most_active_day": most_active_day,
                "most_active_hour": most_active_hour,
                "consistency_score": round(consistency_score, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting study patterns: {e}")
            return {"total_study_time": 0, "average_session_length": 0, "most_active_day": "unknown", "most_active_hour": 0, "consistency_score": 0}

    def _group_activities_into_sessions(self, activities: List[Dict], gap_minutes: int = 30) -> List[Dict]:
        """Group activities into sessions based on time gaps"""
        if not activities:
            return []
        
        # Sort by timestamp
        sorted_activities = sorted(activities, key=lambda x: x["timestamp"] or datetime.min)
        
        sessions = []
        current_session = {
            "start": sorted_activities[0]["timestamp"],
            "activities": [sorted_activities[0]],
            "duration": sorted_activities[0]["duration"]
        }
        
        for activity in sorted_activities[1:]:
            if not activity["timestamp"]:
                continue
                
            # Check if this activity should be part of current session
            time_gap = (activity["timestamp"] - current_session["start"]).total_seconds() / 60
            
            if time_gap <= gap_minutes:
                # Add to current session
                current_session["activities"].append(activity)
                current_session["duration"] += activity["duration"]
            else:
                # Start new session
                sessions.append(current_session)
                current_session = {
                    "start": activity["timestamp"],
                    "activities": [activity],
                    "duration": activity["duration"]
                }
        
        # Add last session
        sessions.append(current_session)
        
        return sessions

    async def _calculate_learning_progress(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate overall learning progress"""
        try:
            # Get documents user has studied
            studied_docs = set()
            
            # From flashcards
            flashcard_collection = mongodb_manager.get_collection("flashcard_reviews")
            async for review in flashcard_collection.find({"user_id": user_id}):
                flashcard_col = self.get_flashcard_collection()
                flashcard = await flashcard_col.find_one({"card_id": review.get("card_id")})
                if flashcard:
                    studied_docs.add(flashcard.get("document_id"))
            
            # From quizzes
            quiz_collection = self.get_quiz_collection()
            async for attempt in quiz_collection.find({"user_id": user_id}):
                quiz_col = mongodb_manager.get_collection("quizzes")
                quiz = await quiz_col.find_one({"quiz_id": attempt.get("quiz_id")})
                if quiz:
                    studied_docs.add(quiz.get("document_id"))
            
            # From chat
            chat_collection = self.get_chat_collection()
            async for chat in chat_collection.find({"user_id": user_id}):
                studied_docs.add(chat.get("document_id"))
            
            # Calculate progress metrics
            total_documents_studied = len(studied_docs)
            
            # Get recent performance trends
            recent_quiz_scores = []
            async for attempt in quiz_collection.find({
                "user_id": user_id,
                "completed_at": {"$gte": start_date, "$lte": end_date}
            }).sort("completed_at", 1):
                recent_quiz_scores.append(attempt.get("percentage", 0))
            
            # Calculate learning velocity (improvement over time)
            learning_velocity = 0
            if len(recent_quiz_scores) > 1:
                # Simple linear regression to find trend
                x_values = list(range(len(recent_quiz_scores)))
                y_values = recent_quiz_scores
                
                n = len(x_values)
                sum_x = sum(x_values)
                sum_y = sum(y_values)
                sum_xy = sum(x * y for x, y in zip(x_values, y_values))
                sum_x2 = sum(x * x for x in x_values)
                
                if n * sum_x2 - sum_x * sum_x != 0:
                    learning_velocity = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Calculate mastery level
            mastery_level = "beginner"
            if total_documents_studied > 10:
                mastery_level = "advanced"
            elif total_documents_studied > 5:
                mastery_level = "intermediate"
            
            return {
                "total_documents_studied": total_documents_studied,
                "learning_velocity": round(learning_velocity, 2),
                "mastery_level": mastery_level,
                "recent_performance": recent_quiz_scores[-5:] if recent_quiz_scores else []
            }
            
        except Exception as e:
            logger.error(f"Error calculating learning progress: {e}")
            return {"total_documents_studied": 0, "learning_velocity": 0, "mastery_level": "beginner", "recent_performance": []}

    async def _calculate_study_streak(self, user_id: str) -> int:
        """Calculate current study streak in days"""
        try:
            # Get all learning activities sorted by date
            activities = []
            
            # Get flashcard reviews
            flashcard_collection = mongodb_manager.get_collection("flashcard_reviews")
            async for review in flashcard_collection.find({"user_id": user_id}):
                if review.get("reviewed_at"):
                    activities.append(review["reviewed_at"])
            
            # Get quiz attempts
            quiz_collection = self.get_quiz_collection()
            async for attempt in quiz_collection.find({"user_id": user_id}):
                if attempt.get("completed_at"):
                    activities.append(attempt["completed_at"])
            
            # Get chat activities
            chat_collection = self.get_chat_collection()
            async for chat in chat_collection.find({"user_id": user_id}):
                if chat.get("created_at"):
                    activities.append(chat["created_at"])
            
            if not activities:
                return 0
            
            # Get unique study dates
            study_dates = set()
            for activity_date in activities:
                study_dates.add(activity_date.date())
            
            # Calculate streak from today backwards
            current_date = datetime.utcnow().date()
            streak = 0
            
            while current_date in study_dates:
                streak += 1
                current_date -= timedelta(days=1)
            
            return streak
            
        except Exception as e:
            logger.error(f"Error calculating study streak: {e}")
            return 0

    async def _generate_study_recommendations(self, user_id: str) -> List[StudyRecommendation]:
        """Generate personalized study recommendations"""
        try:
            recommendations = []
            
            # Analyze recent performance
            quiz_collection = self.get_quiz_collection()
            recent_quiz_attempts = []
            async for attempt in quiz_collection.find({"user_id": user_id}).sort("completed_at", -1).limit(10):
                recent_quiz_attempts.append(attempt)
            
            # Check for weak Bloom's taxonomy areas
            if recent_quiz_attempts:
                bloom_scores = defaultdict(list)
                for attempt in recent_quiz_attempts:
                    for level, score in attempt.get("bloom_scores", {}).items():
                        bloom_scores[level].append(score)
                
                weak_areas = []
                for level, scores in bloom_scores.items():
                    avg_score = sum(scores) / len(scores)
                    if avg_score < 70:
                        weak_areas.append(level)
                
                if weak_areas:
                    recommendations.append(StudyRecommendation(
                        type="skill_focus",
                        title=f"ควรเน้นการฝึกฝนทักษะระดับ {', '.join(weak_areas)}",
                        description=f"คะแนนเฉลี่ยในทักษะเหล่านี้ต่ำกว่า 70%",
                        priority="high"
                    ))
            
            # Check study consistency
            streak = await self._calculate_study_streak(user_id)
            if streak == 0:
                recommendations.append(StudyRecommendation(
                    type="consistency",
                    title="เริ่มสร้างนิสัยการเรียนต่อเนื่อง",
                    description="การเรียนรู้แบบสม่ำเสมอจะช่วยเพิ่มประสิทธิภาพ",
                    priority="medium"
                ))
            elif streak < 3:
                recommendations.append(StudyRecommendation(
                    type="consistency",
                    title="พยายามเรียนต่อเนื่องให้ได้อย่างน้อย 7 วัน",
                    description="การเรียนรู้ต่อเนื่องจะช่วยเสริมสร้างความจำระยะยาว",
                    priority="medium"
                ))
            
            # Check for unused features
            chat_collection = self.get_chat_collection()
            chat_count = await chat_collection.count_documents({"user_id": user_id})
            if chat_count == 0:
                recommendations.append(StudyRecommendation(
                    type="feature_usage",
                    title="ลองใช้ฟีเจอร์ Chat เพื่อถามคำถามเกี่ยวกับเอกสาร",
                    description="การถาม-ตอบจะช่วยเพิ่มความเข้าใจในเนื้อหา",
                    priority="low"
                ))
            
            flashcard_collection = mongodb_manager.get_collection("flashcard_reviews")
            flashcard_count = await flashcard_collection.count_documents({"user_id": user_id})
            if flashcard_count == 0:
                recommendations.append(StudyRecommendation(
                    type="feature_usage",
                    title="ลองใช้ Flashcards เพื่อท่องจำคำศัพท์และแนวคิดสำคัญ",
                    description="Flashcards เป็นวิธีที่มีประสิทธิภาพในการจำ",
                    priority="low"
                ))
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating study recommendations: {e}")
            return []

    async def get_document_analytics(self, document_id: str) -> Dict[str, Any]:
        """Get analytics for a specific document"""
        try:
            # Get document info
            document_collection = self.get_document_collection()
            document = await document_collection.find_one({"document_id": document_id})
            if not document:
                return {"error": "Document not found"}
            
            # Count users who studied this document
            unique_users = set()
            
            # From flashcards
            flashcard_collection = self.get_flashcard_collection()
            flashcards = []
            async for flashcard in flashcard_collection.find({"document_id": document_id}):
                flashcards.append(flashcard)
            
            flashcard_reviews = 0
            if flashcards:
                flashcard_ids = [f["card_id"] for f in flashcards]
                flashcard_review_collection = mongodb_manager.get_collection("flashcard_reviews")
                async for review in flashcard_review_collection.find({"card_id": {"$in": flashcard_ids}}):
                    unique_users.add(review.get("user_id"))
                    flashcard_reviews += 1
            
            # From quizzes
            quizzes = []
            quiz_main_collection = mongodb_manager.get_collection("quizzes")
            async for quiz in quiz_main_collection.find({"document_id": document_id}):
                quizzes.append(quiz)
            
            quiz_attempts = 0
            if quizzes:
                quiz_ids = [q["quiz_id"] for q in quizzes]
                quiz_collection = self.get_quiz_collection()
                async for attempt in quiz_collection.find({"quiz_id": {"$in": quiz_ids}}):
                    unique_users.add(attempt.get("user_id"))
                    quiz_attempts += 1
            
            # From chat
            chat_questions = 0
            chat_collection = self.get_chat_collection()
            async for chat in chat_collection.find({"document_id": document_id}):
                unique_users.add(chat.get("user_id"))
                chat_questions += 1
            
            return {
                "document_id": document_id,
                "document_title": document.get("title", "Unknown"),
                "unique_users": len(unique_users),
                "total_flashcards": len(flashcards),
                "total_flashcard_reviews": flashcard_reviews,
                "total_quizzes": len(quizzes),
                "total_quiz_attempts": quiz_attempts,
                "total_chat_questions": chat_questions,
                "engagement_score": self._calculate_engagement_score(
                    len(unique_users), flashcard_reviews, quiz_attempts, chat_questions
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting document analytics: {e}")
            return {"error": str(e)}

    def _calculate_engagement_score(self, users: int, flashcard_reviews: int, quiz_attempts: int, chat_questions: int) -> float:
        """Calculate engagement score for a document"""
        if users == 0:
            return 0.0
        
        # Weighted average of different activities per user
        activities_per_user = (flashcard_reviews * 0.3 + quiz_attempts * 0.4 + chat_questions * 0.3) / users
        
        # Normalize to 0-100 scale
        engagement_score = min(activities_per_user * 10, 100)
        
        return round(engagement_score, 2)

    async def get_system_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics"""
        try:
            # Count total users (unique from all collections)
            all_users = set()
            
            # From flashcard reviews
            flashcard_collection = mongodb_manager.get_collection("flashcard_reviews")
            async for review in flashcard_collection.find():
                all_users.add(review.get("user_id"))
            
            # From quiz attempts
            quiz_collection = self.get_quiz_collection()
            async for attempt in quiz_collection.find():
                all_users.add(attempt.get("user_id"))
            
            # From chat
            chat_collection = self.get_chat_collection()
            async for chat in chat_collection.find():
                all_users.add(chat.get("user_id"))
            
            total_users = len(all_users)
            
            # Count documents
            document_collection = self.get_document_collection()
            total_documents = await document_collection.count_documents({})
            
            # Count activities
            total_flashcard_reviews = await flashcard_collection.count_documents({})
            total_quiz_attempts = await quiz_collection.count_documents({})
            total_chat_questions = await chat_collection.count_documents({})
            
            # Recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_flashcard_reviews = await flashcard_collection.count_documents({"reviewed_at": {"$gte": week_ago}})
            recent_quiz_attempts = await quiz_collection.count_documents({"completed_at": {"$gte": week_ago}})
            recent_chat_questions = await chat_collection.count_documents({"created_at": {"$gte": week_ago}})
            
            return {
                "total_users": total_users,
                "total_documents": total_documents,
                "total_flashcard_reviews": total_flashcard_reviews,
                "total_quiz_attempts": total_quiz_attempts,
                "total_chat_questions": total_chat_questions,
                "recent_activity": {
                    "flashcard_reviews": recent_flashcard_reviews,
                    "quiz_attempts": recent_quiz_attempts,
                    "chat_questions": recent_chat_questions
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system analytics: {e}")
            return {"error": str(e)}

# Maintain backward compatibility by keeping the original class
class AnalyticsService(AdvancedAnalyticsService):
    """Backward compatible analytics service"""
    pass

# Global instances
analytics_service = AnalyticsService()
advanced_analytics_service = AdvancedAnalyticsService()