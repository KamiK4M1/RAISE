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
from bson import ObjectId
from app.database.mongodb import mongodb_manager, Collections, create_quiz_document, create_quiz_attempt_document
from app.core.exceptions import ModelError

logger = logging.getLogger(__name__)

class QuizGeneratorService:
    def __init__(self):
        self.quiz_collection = mongodb_manager.get_quizzes_collection()
        self.attempt_collection = mongodb_manager.get_quiz_attempts_collection()
        self.document_collection = mongodb_manager.get_documents_collection()

    async def generate_quiz(
        self,
        document_id: str,
        user_id: str,
        request: QuizGenerateRequest
    ) -> QuizModel:
        """Generate a quiz from document content"""
        try:
            document = await self.document_collection.find_one({"_id": ObjectId(document_id)})
            if not document:
                raise ValueError(f"Document {document_id} not found")

            content = document.get("content", "")
            if not content:
                raise ValueError("Document has no content")

            bloom_distribution = request.bloom_distribution or {
                "remember": max(1, request.question_count // 6),
                "understand": max(1, request.question_count // 6),
                "apply": max(1, request.question_count // 6),
                "analyze": max(1, request.question_count // 6),
                "evaluate": max(1, request.question_count // 8),
                "create": max(1, request.question_count // 8)
            }

            total_distributed = sum(bloom_distribution.values())
            if total_distributed != request.question_count:
                max_category = max(bloom_distribution, key=bloom_distribution.get)
                bloom_distribution[max_category] += request.question_count - total_distributed

            raw_questions = await together_ai.generate_quiz_questions(
                content=content,
                count=request.question_count,
                bloom_distribution=bloom_distribution
            )

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

            # Create quiz document
            quiz_document = create_quiz_document(
                document_id=document_id,
                title=f"Quiz: {document.get('title', 'Untitled Document')}",
                description=f"Quiz generated from {document.get('title', 'document')}",
                questions=[q.dict() for q in questions],
                total_points=total_points,
                time_limit=request.time_limit
            )
            
            result = await self.quiz_collection.insert_one(quiz_document)
            quiz_id = str(result.inserted_id)
            
            # Create response model
            quiz = QuizModel(
                quiz_id=quiz_id,
                document_id=document_id,
                title=quiz_document["title"],
                description=quiz_document["description"],
                questions=[q.dict() for q in questions],
                total_points=total_points,
                time_limit=request.time_limit,
                bloom_distribution=bloom_distribution
            )
            
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
        quiz_data = await self.quiz_collection.find_one({"_id": ObjectId(quiz_id)})
        if quiz_data:
            # Convert for response
            quiz_data["quiz_id"] = str(quiz_data["_id"])
            del quiz_data["_id"]
            quiz_data["document_id"] = str(quiz_data["document_id"])
            return QuizModel(**quiz_data)
        return None

    async def submit_quiz(
        self,
        quiz_id: str,
        user_id: str,
        submission: QuizSubmission
    ) -> QuizResults:
        """Submit quiz answers and calculate results"""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {quiz_id} not found")

        attempts_count = await self.attempt_collection.count_documents({
            "quiz_id": quiz_id,
            "user_id": user_id
        })

        if attempts_count >= quiz.attempts_allowed:
            raise ValueError("Maximum attempts exceeded")

        results = self._calculate_results(quiz, submission)
        
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

        await self.attempt_collection.insert_one(attempt.dict(by_alias=True))
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

    def _calculate_results(self, quiz: QuizModel, submission: QuizSubmission) -> Dict[str, Any]:
        """Calculate quiz results"""
        total_points = 0
        earned_points = 0
        bloom_scores = {}
        bloom_totals = {}
        question_results = []

        for i, question_data in enumerate(quiz.questions):
            question = QuizQuestion(**question_data)
            user_answer = submission.answers[i] if i < len(submission.answers) else ""
            is_correct = user_answer.strip().upper() == question.correct_answer.strip().upper()
            points_earned = question.points if is_correct else 0

            total_points += question.points
            earned_points += points_earned

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

        if percentage < 60:
            recommendations.append("ควรทบทวนเนื้อหาพื้นฐานให้มากขึ้น")
        elif percentage < 80:
            recommendations.append("ผลการเรียนรู้อยู่ในระดับที่ดี แต่ยังมีห้องสำหรับการพัฒนา")
        else:
            recommendations.append("ผลการเรียนรู้อยู่ในระดับดีเยี่ยม")

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
        query = {"user_id": user_id}
        if document_id:
            quiz_ids = [quiz["quiz_id"] async for quiz in self.quiz_collection.find({"document_id": document_id})]
            query["quiz_id"] = {"$in": quiz_ids}

        attempts = []
        async for attempt in self.attempt_collection.find(query).sort("completed_at", -1):
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
    
    async def delete_quiz(self, quiz_id: str) -> bool:
        """Delete quiz and all associated attempts"""
        quiz_result = await self.quiz_collection.delete_one({"quiz_id": quiz_id})
        await self.attempt_collection.delete_many({"quiz_id": quiz_id})
        return quiz_result.deleted_count > 0

quiz_generator = QuizGeneratorService()