import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from collections import defaultdict, Counter

from app.database.mongodb import get_collection
from app.models.analytics import UserAnalyticsUpdated as UserAnalytics, LearningSession, StudyRecommendation

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.flashcard_collection = get_collection("flashcards")
        self.quiz_collection = get_collection("quiz_attempts")
        self.chat_collection = get_collection("chat_history")
        self.session_collection = get_collection("learning_sessions")
        self.document_collection = get_collection("documents")

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
            
            result = await self.session_collection.insert_one(session.dict(by_alias=True))
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
            flashcard_collection = get_collection("flashcard_reviews")
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
            attempts = []
            async for attempt in self.quiz_collection.find({
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
                    "bloom_weaknesses": []
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
            return {"total_attempts": 0, "average_score": 0, "improvement_rate": 0, "bloom_strengths": [], "bloom_weaknesses": []}

    async def _get_chat_analytics(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get chat analytics for user"""
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
            flashcard_collection = get_collection("flashcard_reviews")
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
            async for attempt in self.quiz_collection.find({
                "user_id": user_id,
                "completed_at": {"$gte": start_date, "$lte": end_date}
            }):
                activities.append({
                    "type": "quiz",
                    "timestamp": attempt.get("completed_at"),
                    "duration": attempt.get("time_taken", 600)  # seconds
                })
            
            # Chat sessions
            async for chat in self.chat_collection.find({
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
            flashcard_collection = get_collection("flashcard_reviews")
            async for review in flashcard_collection.find({"user_id": user_id}):
                flashcard = await self.flashcard_collection.find_one({"card_id": review.get("card_id")})
                if flashcard:
                    studied_docs.add(flashcard.get("document_id"))
            
            # From quizzes
            async for attempt in self.quiz_collection.find({"user_id": user_id}):
                quiz = await get_collection("quizzes").find_one({"quiz_id": attempt.get("quiz_id")})
                if quiz:
                    studied_docs.add(quiz.get("document_id"))
            
            # From chat
            async for chat in self.chat_collection.find({"user_id": user_id}):
                studied_docs.add(chat.get("document_id"))
            
            # Calculate progress metrics
            total_documents_studied = len(studied_docs)
            
            # Get recent performance trends
            recent_quiz_scores = []
            async for attempt in self.quiz_collection.find({
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
            flashcard_collection = get_collection("flashcard_reviews")
            async for review in flashcard_collection.find({"user_id": user_id}):
                if review.get("reviewed_at"):
                    activities.append(review["reviewed_at"])
            
            # Get quiz attempts
            async for attempt in self.quiz_collection.find({"user_id": user_id}):
                if attempt.get("completed_at"):
                    activities.append(attempt["completed_at"])
            
            # Get chat activities
            async for chat in self.chat_collection.find({"user_id": user_id}):
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
            recent_quiz_attempts = []
            async for attempt in self.quiz_collection.find({"user_id": user_id}).sort("completed_at", -1).limit(10):
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
            chat_count = await self.chat_collection.count_documents({"user_id": user_id})
            if chat_count == 0:
                recommendations.append(StudyRecommendation(
                    type="feature_usage",
                    title="ลองใช้ฟีเจอร์ Chat เพื่อถามคำถามเกี่ยวกับเอกสาร",
                    description="การถาม-ตอบจะช่วยเพิ่มความเข้าใจในเนื้อหา",
                    priority="low"
                ))
            
            flashcard_count = await get_collection("flashcard_reviews").count_documents({"user_id": user_id})
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
            document = await self.document_collection.find_one({"document_id": document_id})
            if not document:
                return {"error": "Document not found"}
            
            # Count users who studied this document
            unique_users = set()
            
            # From flashcards
            flashcards = []
            async for flashcard in self.flashcard_collection.find({"document_id": document_id}):
                flashcards.append(flashcard)
            
            flashcard_reviews = 0
            if flashcards:
                flashcard_ids = [f["card_id"] for f in flashcards]
                flashcard_collection = get_collection("flashcard_reviews")
                async for review in flashcard_collection.find({"card_id": {"$in": flashcard_ids}}):
                    unique_users.add(review.get("user_id"))
                    flashcard_reviews += 1
            
            # From quizzes
            quizzes = []
            quiz_collection = get_collection("quizzes")
            async for quiz in quiz_collection.find({"document_id": document_id}):
                quizzes.append(quiz)
            
            quiz_attempts = 0
            if quizzes:
                quiz_ids = [q["quiz_id"] for q in quizzes]
                async for attempt in self.quiz_collection.find({"quiz_id": {"$in": quiz_ids}}):
                    unique_users.add(attempt.get("user_id"))
                    quiz_attempts += 1
            
            # From chat
            chat_questions = 0
            async for chat in self.chat_collection.find({"document_id": document_id}):
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
            flashcard_collection = get_collection("flashcard_reviews")
            async for review in flashcard_collection.find():
                all_users.add(review.get("user_id"))
            
            # From quiz attempts
            async for attempt in self.quiz_collection.find():
                all_users.add(attempt.get("user_id"))
            
            # From chat
            async for chat in self.chat_collection.find():
                all_users.add(chat.get("user_id"))
            
            total_users = len(all_users)
            
            # Count documents
            total_documents = await self.document_collection.count_documents({})
            
            # Count activities
            total_flashcard_reviews = await flashcard_collection.count_documents({})
            total_quiz_attempts = await self.quiz_collection.count_documents({})
            total_chat_questions = await self.chat_collection.count_documents({})
            
            # Recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_flashcard_reviews = await flashcard_collection.count_documents({"reviewed_at": {"$gte": week_ago}})
            recent_quiz_attempts = await self.quiz_collection.count_documents({"completed_at": {"$gte": week_ago}})
            recent_chat_questions = await self.chat_collection.count_documents({"created_at": {"$gte": week_ago}})
            
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

# Global instance
analytics_service = AnalyticsService()