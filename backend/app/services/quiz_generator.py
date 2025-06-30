import asyncio
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from app.models.quiz import (
    QuizModel, QuizQuestion, QuizAttempt, QuizGenerateRequest, 
    QuizSubmission, QuizResults
)
from app.core.ai_models import together_ai
from app.database.mongodb import get_collection
from app.core.exceptions import ModelError

logger = logging.getLogger(__name__)

class QuizGeneratorService:
    def __init__(self):
        self.quiz_collection = None
        self.attempt_collection = None
        self.document_collection = None
    
    def _ensure_collections(self):
        """Lazy initialization of collections"""
        if self.quiz_collection is None:
            self.quiz_collection = get_collection("quizzes")
            self.attempt_collection = get_collection("quiz_attempts")
            self.document_collection = get_collection("documents")

    async def generate_quiz(
        self,
        document_id: str,
        user_id: str,
        request: QuizGenerateRequest
    ) -> QuizModel:
        """Generate a quiz from document content"""
        try:
            self._ensure_collections()
            # Get document content
            document = await self.document_collection.find_one({"document_id": document_id})
            if not document:
                raise ValueError(f"Document {document_id} not found")

            content = document.get("content", "")
            if not content:
                raise ValueError("Document has no content")

            # Use default bloom distribution if not provided
            bloom_distribution = request.bloom_distribution or {
                "remember": max(1, request.question_count // 6),
                "understand": max(1, request.question_count // 6),
                "apply": max(1, request.question_count // 6),
                "analyze": max(1, request.question_count // 6),
                "evaluate": max(1, request.question_count // 8),
                "create": max(1, request.question_count // 8)
            }

            # Adjust distribution to match requested count
            total_distributed = sum(bloom_distribution.values())
            if total_distributed != request.question_count:
                # Adjust the largest category
                max_category = max(bloom_distribution, key=bloom_distribution.get)
                bloom_distribution[max_category] += request.question_count - total_distributed

            # Generate questions using AI
            raw_questions = await together_ai.generate_quiz_questions(
                content=content,
                count=request.question_count,
                bloom_distribution=bloom_distribution
            )

            # Convert to QuizQuestion objects
            questions = []
            total_points = 0
            
            for i, q in enumerate(raw_questions):
                question = QuizQuestion(
                    question_id=str(uuid.uuid4()),
                    question=q.get("question", ""),
                    options=q.get("options", []),
                    correct_answer=q.get("correct_answer", "A"),
                    explanation=q.get("explanation", ""),
                    bloom_level=q.get("bloom_level", "remember"),
                    difficulty=q.get("difficulty", request.difficulty),
                    points=self._get_points_for_bloom_level(q.get("bloom_level", "remember"))
                )
                questions.append(question)
                total_points += question.points

            # Create quiz model
            quiz_id = str(uuid.uuid4())
            quiz = QuizModel(
                quiz_id=quiz_id,
                document_id=document_id,
                title=f"Quiz: {document.get('title', 'Untitled Document')}",
                description=f"Quiz generated from {document.get('title', 'document')}",
                questions=questions,
                total_points=total_points,
                time_limit=request.time_limit,
                bloom_distribution=bloom_distribution
            )

            # Save to database
            await self.quiz_collection.insert_one(quiz.dict(by_alias=True))
            
            logger.info(f"Generated quiz {quiz_id} with {len(questions)} questions")
            return quiz

        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            raise ModelError(f"Failed to generate quiz: {str(e)}")

    def _get_points_for_bloom_level(self, bloom_level: str) -> int:
        """Get points based on Bloom's taxonomy level"""
        points_map = {
            "remember": 1,
            "understand": 1,
            "apply": 2,
            "analyze": 2,
            "evaluate": 3,
            "create": 3
        }
        return points_map.get(bloom_level, 1)

    async def get_quiz(self, quiz_id: str) -> Optional[QuizModel]:
        """Get quiz by ID"""
        try:
            self._ensure_collections()
            quiz_data = await self.quiz_collection.find_one({"quiz_id": quiz_id})
            if quiz_data:
                return QuizModel(**quiz_data)
            return None
        except Exception as e:
            logger.error(f"Error getting quiz {quiz_id}: {e}")
            return None

    async def submit_quiz(
        self,
        quiz_id: str,
        user_id: str,
        submission: QuizSubmission
    ) -> QuizResults:
        """Submit quiz answers and calculate results"""
        try:
            self._ensure_collections()
            # Get quiz
            quiz = await self.get_quiz(quiz_id)
            if not quiz:
                raise ValueError(f"Quiz {quiz_id} not found")

            # Check if user has attempts left
            attempts_count = await self.attempt_collection.count_documents({
                "quiz_id": quiz_id,
                "user_id": user_id
            })

            if attempts_count >= quiz.attempts_allowed:
                raise ValueError("Maximum attempts exceeded")

            # Calculate results
            results = self._calculate_results(quiz, submission)
            
            # Create attempt record
            attempt = QuizAttempt(
                attempt_id=str(uuid.uuid4()),
                quiz_id=quiz_id,
                user_id=user_id,
                answers=submission.answers,
                score=results["score"],
                total_points=results["total_points"],
                percentage=results["percentage"],
                time_taken=submission.time_taken,
                bloom_scores=results["bloom_scores"],
                question_results=results["question_results"]
            )

            # Save attempt
            await self.attempt_collection.insert_one(attempt.dict(by_alias=True))

            # Generate recommendations
            recommendations = self._generate_recommendations(results)

            return QuizResults(
                attempt_id=attempt.attempt_id,
                quiz_id=quiz_id,
                score=results["score"],
                percentage=results["percentage"],
                total_points=results["total_points"],
                time_taken=submission.time_taken,
                bloom_scores=results["bloom_scores"],
                question_results=results["question_results"],
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Error submitting quiz: {e}")
            raise ModelError(f"Failed to submit quiz: {str(e)}")

    def _calculate_results(self, quiz: QuizModel, submission: QuizSubmission) -> Dict[str, Any]:
        """Calculate quiz results"""
        total_points = 0
        earned_points = 0
        bloom_scores = {}
        bloom_totals = {}
        question_results = []

        for i, question in enumerate(quiz.questions):
            user_answer = submission.answers[i] if i < len(submission.answers) else ""
            is_correct = user_answer.strip().upper() == question.correct_answer.strip().upper()
            points_earned = question.points if is_correct else 0

            total_points += question.points
            earned_points += points_earned

            # Track bloom level scores
            bloom_level = question.bloom_level
            if bloom_level not in bloom_scores:
                bloom_scores[bloom_level] = 0
                bloom_totals[bloom_level] = 0
            
            bloom_scores[bloom_level] += points_earned
            bloom_totals[bloom_level] += question.points

            question_results.append({
                "question_id": question.question_id,
                "question": question.question,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "points_earned": points_earned,
                "points_possible": question.points,
                "bloom_level": bloom_level,
                "explanation": question.explanation
            })

        # Calculate bloom level percentages
        bloom_percentages = {}
        for level in bloom_scores:
            if bloom_totals[level] > 0:
                bloom_percentages[level] = (bloom_scores[level] / bloom_totals[level]) * 100
            else:
                bloom_percentages[level] = 0

        percentage = (earned_points / total_points * 100) if total_points > 0 else 0

        return {
            "score": earned_points,
            "total_points": total_points,
            "percentage": round(percentage, 2),
            "bloom_scores": bloom_percentages,
            "question_results": question_results
        }

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate study recommendations based on results"""
        recommendations = []
        bloom_scores = results["bloom_scores"]
        percentage = results["percentage"]

        # Overall performance recommendations
        if percentage < 60:
            recommendations.append("ควรทบทวนเนื้อหาพื้นฐานให้มากขึ้น")
        elif percentage < 80:
            recommendations.append("ผลการเรียนรู้อยู่ในระดับที่ดี แต่ยังมีห้องสำหรับการพัฒนา")
        else:
            recommendations.append("ผลการเรียนรู้อยู่ในระดับดีเยี่ยม")

        # Bloom level specific recommendations
        weak_areas = [level for level, score in bloom_scores.items() if score < 70]
        
        for level in weak_areas:
            if level == "remember":
                recommendations.append("ควรทบทวนข้อเท็จจริงและคำนิยามพื้นฐาน")
            elif level == "understand":
                recommendations.append("ควรฝึกการอธิบายและสรุปเนื้อหา")
            elif level == "apply":
                recommendations.append("ควรฝึกการประยุกต์ใช้ความรู้ในสถานการณ์ใหม่")
            elif level == "analyze":
                recommendations.append("ควรฝึกการวิเคราะห์และเปรียบเทียบ")
            elif level == "evaluate":
                recommendations.append("ควรฝึกการประเมินและตัดสินใจ")
            elif level == "create":
                recommendations.append("ควรฝึกการสร้างสรรค์และออกแบบ")

        return recommendations

    async def get_quiz_history(self, user_id: str, document_id: Optional[str] = None) -> List[Dict]:
        """Get quiz attempt history for user"""
        try:
            self._ensure_collections()
            query = {"user_id": user_id}
            if document_id:
                # Get quizzes for specific document
                quiz_ids = []
                async for quiz in self.quiz_collection.find({"document_id": document_id}):
                    quiz_ids.append(quiz["quiz_id"])
                query["quiz_id"] = {"$in": quiz_ids}

            attempts = []
            async for attempt in self.attempt_collection.find(query).sort("completed_at", -1):
                # Get quiz info
                quiz = await self.quiz_collection.find_one({"quiz_id": attempt["quiz_id"]})
                attempt_data = {
                    "attempt_id": attempt["attempt_id"],
                    "quiz_id": attempt["quiz_id"],
                    "quiz_title": quiz.get("title", "Unknown Quiz") if quiz else "Unknown Quiz",
                    "score": attempt["score"],
                    "total_points": attempt["total_points"],
                    "percentage": attempt["percentage"],
                    "time_taken": attempt["time_taken"],
                    "completed_at": attempt["completed_at"]
                }
                attempts.append(attempt_data)

            return attempts

        except Exception as e:
            logger.error(f"Error getting quiz history: {e}")
            return []

    async def get_quiz_analytics(self, quiz_id: str) -> Dict[str, Any]:
        """Get analytics for a specific quiz"""
        try:
            self._ensure_collections()
            # Get all attempts for this quiz
            attempts = []
            async for attempt in self.attempt_collection.find({"quiz_id": quiz_id}):
                attempts.append(attempt)

            if not attempts:
                return {"total_attempts": 0}

            # Calculate statistics
            scores = [attempt["percentage"] for attempt in attempts]
            avg_score = sum(scores) / len(scores)
            
            # Bloom level analysis
            bloom_analysis = {}
            for attempt in attempts:
                for level, score in attempt.get("bloom_scores", {}).items():
                    if level not in bloom_analysis:
                        bloom_analysis[level] = []
                    bloom_analysis[level].append(score)

            bloom_averages = {}
            for level, scores in bloom_analysis.items():
                bloom_averages[level] = sum(scores) / len(scores) if scores else 0

            return {
                "total_attempts": len(attempts),
                "average_score": round(avg_score, 2),
                "highest_score": max(scores),
                "lowest_score": min(scores),
                "bloom_averages": bloom_averages,
                "completion_rate": len([s for s in scores if s >= 60]) / len(scores) * 100
            }

        except Exception as e:
            logger.error(f"Error getting quiz analytics: {e}")
            return {"error": str(e)}

    async def delete_quiz(self, quiz_id: str) -> bool:
        """Delete quiz and all associated attempts"""
        try:
            self._ensure_collections()
            # Delete quiz
            quiz_result = await self.quiz_collection.delete_one({"quiz_id": quiz_id})
            
            # Delete associated attempts
            await self.attempt_collection.delete_many({"quiz_id": quiz_id})
            
            return quiz_result.deleted_count > 0

        except Exception as e:
            logger.error(f"Error deleting quiz {quiz_id}: {e}")
            return False

# Global instance
quiz_generator = QuizGeneratorService()