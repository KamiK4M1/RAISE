"""
AI-Powered Quiz Generator with Bloom's Taxonomy Support
Supports Thai and English content generation with intelligent difficulty balancing
"""

import asyncio
import json
import logging
import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
import datetime
from datetime import timezone
from enum import Enum

from app.models.quiz import (
    QuizModel, QuizQuestion, QuizAttempt, QuizGenerateRequest,
    QuizSubmission, QuizResults
)
from app.core.ai_models import together_ai
from bson import ObjectId
from app.database.mongodb import mongodb_manager, Collections, create_quiz_document, create_quiz_attempt_document
from app.core.exceptions import ModelError

logger = logging.getLogger(__name__)


class BloomLevel(str, Enum):
    """Bloom's Taxonomy levels with Thai translations"""
    REMEMBER = "remember"
    UNDERSTAND = "understand"  
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class QuestionType(str, Enum):
    """Question types supported"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class DifficultyLevel(str, Enum):
    """Difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BloomPromptTemplates:
    """Sophisticated prompt templates for each Bloom's taxonomy level"""
    
    @staticmethod
    def get_system_prompt() -> str:
        return """คุณเป็นผู้เชี่ยวชาญด้านการสร้างข้อสอบที่มีคุณภาพสูงตาม Bloom's Taxonomy 
        สร้างคำถามที่มีความหลากหลาย ชัดเจน และวัดความรู้ความเข้าใจได้อย่างแม่นยำ
        ให้ความสำคัญกับการใช้ภาษาไทยที่ถูกต้องและเหมาะสม
        
        หลักการสำคัญ:
        1. คำถามต้องมีความชัดเจนและไม่กำกวม
        2. ตัวเลือกต้องมีความน่าเชื่อและเป็นไปได้จริง
        3. คำอธิบายต้องให้เหตุผลที่ชัดเจน
        4. ใช้ภาษาที่เหมาะสมกับระดับความยาก
        5. หลีกเลี่ยงคำถามที่ตอบได้หลายความหมาย"""

    @staticmethod
    def get_bloom_prompt(level: BloomLevel, content: str, question_count: int, 
                        question_type: QuestionType, difficulty: DifficultyLevel,
                        language: str = "thai") -> str:
        """Generate level-specific prompts with sophisticated instructions"""
        
        level_configs = {
            BloomLevel.REMEMBER: {
                "thai_description": "จำ - ความจำ การระลึก ข้อเท็จจริง",
                "keywords": ["นิยาม", "อะไร", "ใคร", "เมื่อไหร่", "ที่ไหน", "ระบุ", "แสดงรายการ"],
                "instructions": "สร้างคำถามที่ทดสอบความจำและการระลึกข้อเท็จจริงพื้นฐาน เช่น คำนิยาม วันที่ ชื่อ สูตร"
            },
            BloomLevel.UNDERSTAND: {
                "thai_description": "เข้าใจ - การตีความ การอธิบาย การสรุป",
                "keywords": ["อธิบาย", "สรุป", "แปลความ", "เปรียบเทียบ", "จำแนก", "ยกตัวอย่าง"],
                "instructions": "สร้างคำถามที่ทดสอบความเข้าใจและการตีความ เช่น การอธิบายแนวคิด การสรุปใจความ"
            },
            BloomLevel.APPLY: {
                "thai_description": "ประยุกต์ - การนำไปใช้ในสถานการณ์ใหม่",
                "keywords": ["ใช้", "แก้ปัญหา", "คำนวณ", "ประยุกต์", "ดำเนินการ", "แสดงวิธี"],
                "instructions": "สร้างคำถามที่ทดสอบการนำความรู้ไปใช้ในสถานการณ์ใหม่ เช่น การแก้ปัญหา การคำนวณ"
            },
            BloomLevel.ANALYZE: {
                "thai_description": "วิเคราะห์ - การแยกแยะส่วนประกอบ การเปรียบเทียบ",
                "keywords": ["วิเคราะห์", "แยกแยะ", "เปรียบเทียบ", "ตรวจสอบ", "สืบค้น", "จัดกลุ่ม"],
                "instructions": "สร้างคำถามที่ทดสอบการวิเคราะห์และแยกแยะส่วนประกอบ เช่น การเปรียบเทียบ การจำแนกประเภท"
            },
            BloomLevel.EVALUATE: {
                "thai_description": "ประเมิน - การตัดสิน การวิจารณ์ การให้คะแนน",
                "keywords": ["ประเมิน", "วิจารณ์", "ตัดสิน", "ให้ความเห็น", "แนะนำ", "เลือก"],
                "instructions": "สร้างคำถามที่ทดสอบการตัดสินใจและการประเมินค่า เช่น การวิจารณ์ การให้ความเห็น"
            },
            BloomLevel.CREATE: {
                "thai_description": "สร้างสรรค์ - การสร้างใหม่ การออกแบบ การวางแผน",
                "keywords": ["สร้าง", "ออกแบบ", "วางแผน", "ประดิษฐ์", "เสนอ", "พัฒนา"],
                "instructions": "สร้างคำถามที่ทดสอบความคิดสร้างสรรค์และการสร้างใหม่ เช่น การออกแบบ การวางแผน"
            }
        }
        
        config = level_configs[level]
        
        difficulty_instructions = {
            DifficultyLevel.EASY: "ระดับง่าย: ใช้คำศัพท์พื้นฐาน โจทย์ตรงไปตรงมา",
            DifficultyLevel.MEDIUM: "ระดับปานกลาง: ต้องคิดวิเคราะห์เล็กน้อย มีการเชื่อมโยง",
            DifficultyLevel.HARD: "ระดับยาก: ต้องคิดวิเคราะห์ลึก มีการประยุกต์ใช้ความรู้หลายด้าน"
        }
        
        question_type_format = {
            QuestionType.MULTIPLE_CHOICE: """
[
  {
    "question_id": "generated_id_will_be_replaced",
    "question": "คำถาม",
    "options": ["A) ตัวเลือก 1", "B) ตัวเลือก 2", "C) ตัวเลือก 3", "D) ตัวเลือก 4"],
    "correct_answer": "A",
    "explanation": "คำอธิบายเหตุผลที่ละเอียด",
    "bloom_level": "%s",
    "difficulty": "%s",
    "question_type": "multiple_choice",
    "quality_score": 0.85
  }
]""" % (level.value, difficulty.value),
            
            QuestionType.TRUE_FALSE: """
[
  {
    "question_id": "generated_id_will_be_replaced",
    "question": "ข้อความ (จริงหรือเท็จ)",
    "options": ["A) จริง", "B) เท็จ"],
    "correct_answer": "A",
    "explanation": "คำอธิบายเหตุผลที่ละเอียด",
    "bloom_level": "%s",
    "difficulty": "%s",
    "question_type": "true_false",
    "quality_score": 0.80
  }
]""" % (level.value, difficulty.value),
            
            QuestionType.SHORT_ANSWER: """
[
  {
    "question_id": "generated_id_will_be_replaced",
    "question": "คำถามที่ต้องตอบแบบสั้น",
    "options": [],
    "correct_answer": "คำตอบที่ถูกต้อง",
    "explanation": "คำอธิบายและเกณฑ์การให้คะแนน",
    "bloom_level": "%s",
    "difficulty": "%s",
    "question_type": "short_answer",
    "quality_score": 0.90
  }
]""" % (level.value, difficulty.value)
        }
        
        return f"""สร้างคำถามระดับ {config['thai_description']} จำนวน {question_count} ข้อ

เนื้อหาอ้างอิง:
{content}

ระดับความยาก: {difficulty_instructions[difficulty]}

คำแนะนำการสร้างคำถาม:
{config['instructions']}

คำสำคัญที่ควรใช้: {', '.join(config['keywords'])}

กรุณาสร้างคำถามที่:
1. มีความชัดเจนและไม่กำกวม
2. ตัวเลือกที่ผิดต้องดูน่าเชื่อ (เป็น distractors ที่ดี)
3. คำอธิบายต้องให้เหตุผลที่ชัดเจน
4. ใช้ภาษาไทยที่ถูกต้องและเหมาะสม
5. เชื่อมโยงกับเนื้อหาที่ให้มาโดยตรง

ตอบในรูปแบบ JSON array เท่านั้น:
{question_type_format[question_type]}"""


class QuestionValidator:
    """Advanced question validation and quality scoring"""
    
    @staticmethod
    def validate_question(question_data: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """Validate question quality and return score with feedback"""
        issues = []
        score = 1.0
        
        # Required fields validation
        required_fields = ["question", "options", "correct_answer", "explanation", "bloom_level"]
        for field in required_fields:
            if field not in question_data:
                issues.append(f"Missing required field: {field}")
                score -= 0.2
        
        if issues:
            return False, max(0, score), issues
        
        # Question text quality
        question_text = question_data["question"]
        if len(question_text) < 10:
            issues.append("Question too short")
            score -= 0.1
        
        if len(question_text) > 300:
            issues.append("Question too long")
            score -= 0.1
        
        # Check for ambiguous words
        ambiguous_patterns = [
            r'\b(บางครั้ง|อาจจะ|มักจะ|โดยทั่วไป)\b',
            r'\b(เสมอ|ไม่เคย|ทั้งหมด|ไม่มีเลย)\b'
        ]
        
        for pattern in ambiguous_patterns:
            if re.search(pattern, question_text):
                score -= 0.05
        
        # Options validation (for multiple choice)
        if question_data.get("question_type") == "multiple_choice":
            options = question_data.get("options", [])
            
            if len(options) < 3:
                issues.append("Insufficient options for multiple choice")
                score -= 0.2
            
            # Check option length balance
            option_lengths = [len(opt.replace(r'^[A-D]\)\s*', '')) for opt in options]
            if max(option_lengths) - min(option_lengths) > 50:
                score -= 0.1
                issues.append("Unbalanced option lengths")
        
        # Explanation quality
        explanation = question_data.get("explanation", "")
        if len(explanation) < 20:
            issues.append("Explanation too brief")
            score -= 0.1
        
        # Bloom level verification
        bloom_level = question_data.get("bloom_level", "")
        if bloom_level not in [level.value for level in BloomLevel]:
            issues.append("Invalid Bloom's taxonomy level")
            score -= 0.2
        
        return len(issues) == 0, max(0, score), issues

    @staticmethod
    def validate_thai_grammar(text: str) -> Tuple[bool, List[str]]:
        """Basic Thai language validation"""
        issues = []
        
        # Check for mixed scripts inappropriately
        if re.search(r'[ก-๙][a-zA-Z][ก-๙]', text):
            issues.append("Inappropriate mixing of Thai and English characters")
        
        # Check for proper spacing around punctuation
        if re.search(r'[ก-๙][.!?][ก-๙]', text):
            issues.append("Missing space after punctuation")
        
        # Check for repeated spaces
        if re.search(r'\s{2,}', text):
            issues.append("Multiple consecutive spaces")
        
        return len(issues) == 0, issues


class AdvancedQuizGenerator:
    """Advanced AI-powered quiz generator with Bloom's taxonomy support"""
    
    def __init__(self):
        self.ai_client = together_ai
        self.prompt_templates = BloomPromptTemplates()
        self.validator = QuestionValidator()
        
    async def generate_enhanced_quiz(
        self,
        content: str,
        question_count: int = 10,
        bloom_distribution: Optional[Dict[str, int]] = None,
        difficulty_distribution: Optional[Dict[str, float]] = None,
        question_types: Optional[List[QuestionType]] = None,
        language: str = "thai",
        quality_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Generate a comprehensive quiz with intelligent distribution
        
        Args:
            content: Source content for questions
            question_count: Total number of questions
            bloom_distribution: Custom Bloom's level distribution
            difficulty_distribution: Difficulty level percentages
            question_types: Allowed question types
            language: Output language (thai/english)
            quality_threshold: Minimum quality score for questions
        """
        
        # Set default distributions
        if bloom_distribution is None:
            bloom_distribution = self._get_default_bloom_distribution(question_count)
        
        if difficulty_distribution is None:
            difficulty_distribution = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
        
        if question_types is None:
            question_types = [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]
        
        all_questions = []
        generation_tasks = []
        
        # Generate questions for each Bloom level
        for bloom_level, count in bloom_distribution.items():
            if count > 0:
                # Distribute difficulty levels
                level_difficulties = self._distribute_difficulty(count, difficulty_distribution)
                
                for difficulty, diff_count in level_difficulties.items():
                    if diff_count > 0:
                        # Distribute question types
                        type_distribution = self._distribute_question_types(diff_count, question_types)
                        
                        for q_type, type_count in type_distribution.items():
                            if type_count > 0:
                                task = self._generate_questions_for_level(
                                    content=content,
                                    bloom_level=BloomLevel(bloom_level),
                                    difficulty=DifficultyLevel(difficulty),
                                    question_type=q_type,
                                    count=type_count,
                                    language=language
                                )
                                generation_tasks.append(task)
        
        # Execute generation tasks sequentially to avoid rate limits
        # results = await asyncio.gather(*generation_tasks, return_exceptions=True)
        results = []
        for task in generation_tasks:
            try:
                result = await task
                results.append(result)
                # Small delay between requests to avoid rate limiting
                await asyncio.sleep(1)
            except Exception as e:
                results.append(e)
        
        # Process and validate results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Question generation failed: {result}")
                continue
            
            for question in result:
                is_valid, quality_score, issues = self.validator.validate_question(question)
                
                if is_valid and quality_score >= quality_threshold:
                    question["quality_score"] = quality_score
                    all_questions.append(question)
                else:
                    logger.warning(f"Question rejected (score: {quality_score}): {issues}")
        
        # Ensure we have enough questions
        if len(all_questions) < question_count * 0.8:  # Allow 20% shortage
            logger.warning(f"Generated only {len(all_questions)} out of {question_count} requested questions")
            
            # Generate additional questions if needed
            additional_needed = question_count - len(all_questions)
            if additional_needed > 0:
                additional_questions = await self._generate_fallback_questions(
                    content, additional_needed, language
                )
                all_questions.extend(additional_questions)
        
        # Sort and return final question set
        final_questions = sorted(all_questions, key=lambda x: (x["bloom_level"], x["difficulty"]))
        return final_questions[:question_count]
    
    async def _generate_questions_for_level(
        self,
        content: str,
        bloom_level: BloomLevel,
        difficulty: DifficultyLevel,
        question_type: QuestionType,
        count: int,
        language: str
    ) -> List[Dict[str, Any]]:
        """Generate questions for specific level, difficulty, and type"""
        
        try:
            system_prompt = self.prompt_templates.get_system_prompt()
            user_prompt = self.prompt_templates.get_bloom_prompt(
                level=bloom_level,
                content=content,
                question_count=count,
                question_type=question_type,
                difficulty=difficulty,
                language=language
            )
            
            response = await self.ai_client.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1500,
                retry_count=5
            )
            
            # Parse JSON response
            try:
                questions = json.loads(response)
                
                # Ensure questions have required metadata
                for question in questions:
                    question.setdefault("bloom_level", bloom_level.value)
                    question.setdefault("difficulty", difficulty.value)
                    question.setdefault("question_type", question_type.value)
                    question.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
                
                return questions
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed for {bloom_level}-{difficulty}-{question_type}: {e}")
                # Try to extract JSON from response if it's embedded in text
                try:
                    import re
                    json_match = re.search(r'\[.*\]', response, re.DOTALL)
                    if json_match:
                        questions = json.loads(json_match.group())
                        # Ensure questions have required metadata
                        for question in questions:
                            question.setdefault("bloom_level", bloom_level.value)
                            question.setdefault("difficulty", difficulty.value)
                            question.setdefault("question_type", question_type.value)
                            question.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
                            question.setdefault("question_id", str(uuid.uuid4()))
                        return questions
                except:
                    pass
                return self._create_fallback_question(bloom_level, difficulty, question_type, content)
                
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return self._create_fallback_question(bloom_level, difficulty, question_type, content)
    
    def _get_default_bloom_distribution(self, total_questions: int) -> Dict[str, int]:
        """Get balanced Bloom's taxonomy distribution"""
        
        base_distribution = {
            "remember": 0.20,     # 20% - foundational knowledge
            "understand": 0.25,   # 25% - comprehension
            "apply": 0.20,        # 20% - application
            "analyze": 0.15,      # 15% - analysis
            "evaluate": 0.10,     # 10% - evaluation
            "create": 0.10        # 10% - creation
        }
        
        distribution = {}
        allocated = 0
        
        for level, percentage in base_distribution.items():
            count = max(1, int(total_questions * percentage))
            distribution[level] = count
            allocated += count
        
        # Adjust for any rounding differences
        difference = total_questions - allocated
        if difference != 0:
            # Add/subtract from the largest category
            max_level = max(distribution.keys(), key=lambda k: distribution[k])
            distribution[max_level] += difference
        
        return distribution
    
    def _distribute_difficulty(self, count: int, distribution: Dict[str, float]) -> Dict[str, int]:
        """Distribute questions across difficulty levels"""
        
        result = {}
        allocated = 0
        
        for difficulty, percentage in distribution.items():
            amount = max(0, int(count * percentage))
            result[difficulty] = amount
            allocated += amount
        
        # Handle remainder
        remainder = count - allocated
        if remainder > 0:
            # Distribute remainder to medium difficulty first
            if "medium" in result:
                result["medium"] += remainder
            else:
                # Fall back to first available difficulty
                first_key = next(iter(result.keys()))
                result[first_key] += remainder
        
        return result
    
    def _distribute_question_types(self, count: int, types: List[QuestionType]) -> Dict[QuestionType, int]:
        """Distribute questions across question types"""
        
        if not types:
            return {QuestionType.MULTIPLE_CHOICE: count}
        
        per_type = count // len(types)
        remainder = count % len(types)
        
        result = {}
        for i, q_type in enumerate(types):
            result[q_type] = per_type + (1 if i < remainder else 0)
        
        return result
    
    def _create_fallback_question(
        self,
        bloom_level: BloomLevel,
        difficulty: DifficultyLevel,
        question_type: QuestionType,
        content: str
    ) -> List[Dict[str, Any]]:
        """Create fallback question when AI generation fails"""
        
        fallback_question = {
            "question_id": str(uuid.uuid4()),
            "question": f"คำถามตัวอย่างระดับ {bloom_level.value} ({difficulty.value})",
            "options": ["A) ตัวเลือก 1", "B) ตัวเลือก 2", "C) ตัวเลือก 3", "D) ตัวเลือก 4"],
            "correct_answer": "A",
            "explanation": f"คำอธิบายสำหรับคำถามระดับ {bloom_level.value}",
            "bloom_level": bloom_level.value,
            "difficulty": difficulty.value,
            "question_type": question_type.value,
            "quality_score": 0.5,
            "is_fallback": True,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return [fallback_question]
    
    async def _generate_fallback_questions(
        self,
        content: str,
        count: int,
        language: str
    ) -> List[Dict[str, Any]]:
        """Generate additional questions when quota not met"""
        
        questions = []
        bloom_levels = list(BloomLevel)
        
        for i in range(count):
            bloom_level = bloom_levels[i % len(bloom_levels)]
            difficulty = DifficultyLevel.MEDIUM
            question_type = QuestionType.MULTIPLE_CHOICE
            
            fallback = self._create_fallback_question(bloom_level, difficulty, question_type, content)
            questions.extend(fallback)
        
        return questions
    
    async def generate_explanations(self, questions: List[Dict[str, Any]], content: str) -> List[Dict[str, Any]]:
        """Generate detailed explanations for questions"""
        
        enhanced_questions = []
        
        for question in questions:
            try:
                explanation_prompt = f"""
เนื้อหาอ้างอิง: {content}

คำถาม: {question['question']}
คำตอบที่ถูกต้อง: {question['correct_answer']}

กรุณาสร้างคำอธิบายที่ละเอียดและครอบคลุม:
1. เหตุผลที่คำตอบนี้ถูกต้อง
2. เหตุผลที่ตัวเลือกอื่นๆ ผิด
3. แนวคิดที่เกี่ยวข้อง
4. ตัวอย่างเพิ่มเติม (ถ้ามี)

ใช้ภาษาไทยที่ชัดเจนและเข้าใจง่าย
"""
                
                enhanced_explanation = await self.ai_client.generate_response(
                    prompt=explanation_prompt,
                    system_prompt="คุณเป็นครูที่เชี่ยวชาญในการอธิบายแนวคิดต่างๆ ให้เข้าใจง่าย",
                    temperature=0.5,
                    max_tokens=1000,
                    retry_count=3
                )
                
                question["detailed_explanation"] = enhanced_explanation
                question["explanation_generated"] = True
                
            except Exception as e:
                logger.error(f"Failed to generate enhanced explanation: {e}")
                question["explanation_generated"] = False
            
            enhanced_questions.append(question)
        
        return enhanced_questions
    
    async def validate_quiz_quality(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive quiz quality assessment"""
        
        total_questions = len(questions)
        if total_questions == 0:
            return {"overall_score": 0, "issues": ["No questions generated"]}
        
        # Calculate quality metrics
        quality_scores = [q.get("quality_score", 0.5) for q in questions]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Check Bloom's distribution
        bloom_counts = {}
        for question in questions:
            level = question.get("bloom_level", "unknown")
            bloom_counts[level] = bloom_counts.get(level, 0) + 1
        
        # Check difficulty distribution
        difficulty_counts = {}
        for question in questions:
            diff = question.get("difficulty", "unknown")
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        
        # Identify issues
        issues = []
        if avg_quality < 0.7:
            issues.append("Overall question quality below threshold")
        
        if len(bloom_counts) < 4:
            issues.append("Insufficient Bloom's taxonomy coverage")
        
        if max(bloom_counts.values()) / total_questions > 0.5:
            issues.append("Unbalanced Bloom's level distribution")
        
        return {
            "overall_score": avg_quality,
            "total_questions": total_questions,
            "bloom_distribution": bloom_counts,
            "difficulty_distribution": difficulty_counts,
            "average_quality": avg_quality,
            "issues": issues,
            "recommendations": self._generate_quality_recommendations(bloom_counts, difficulty_counts, issues)
        }
    
    def _generate_quality_recommendations(
        self,
        bloom_counts: Dict[str, int],
        difficulty_counts: Dict[str, int],
        issues: List[str]
    ) -> List[str]:
        """Generate improvement recommendations"""
        
        recommendations = []
        
        if "Insufficient Bloom's taxonomy coverage" in issues:
            missing_levels = set([level.value for level in BloomLevel]) - set(bloom_counts.keys())
            recommendations.append(f"Add questions for missing Bloom's levels: {missing_levels}")
        
        if "Unbalanced Bloom's level distribution" in issues:
            recommendations.append("Rebalance questions across Bloom's taxonomy levels")
        
        if "Overall question quality below threshold" in issues:
            recommendations.append("Review and improve question clarity and option quality")
        
        # Check for missing difficulty levels
        expected_difficulties = {"easy", "medium", "hard"}
        missing_difficulties = expected_difficulties - set(difficulty_counts.keys())
        if missing_difficulties:
            recommendations.append(f"Add questions with difficulty levels: {missing_difficulties}")
        
        return recommendations


class QuizGeneratorService:
    def __init__(self):
        self.quiz_collection = mongodb_manager.get_quizzes_collection()
        self.attempt_collection = mongodb_manager.get_quiz_attempts_collection()
        self.document_collection = mongodb_manager.get_documents_collection()
        self.advanced_generator = AdvancedQuizGenerator()

    def _parse_llm_json_response(self, response: str) -> List[Dict[str, Any]]:
        """
        A robust parser to extract and validate multiple JSON objects from a raw LLM response string.
        This function is designed to handle common LLM formatting errors, such as:
        - Missing commas between objects.
        - Extraneous text before or after the main JSON array.
        - Trailing commas.
        """
        try:
            import json
            import re

            # 1. Find the main JSON array in the response string.
            # This helps to discard any introductory or concluding text from the LLM.
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if not match:
                logger.warning("Could not find a JSON array (e.g., '[...]') in the LLM response.")
                return []
            
            json_string = match.group(0)

            # 2. Manually extract individual JSON objects.
            # This is more robust than a simple split, as it respects nested structures.
            objects = []
            nesting_level = 0
            start_index = -1

            for i, char in enumerate(json_string):
                if char == '{':
                    if nesting_level == 0:
                        start_index = i
                    nesting_level += 1
                elif char == '}':
                    nesting_level -= 1
                    if nesting_level == 0 and start_index != -1:
                        # We've found a complete top-level object.
                        obj_str = json_string[start_index:i+1]
                        try:
                            # Validate that the extracted string is indeed a valid JSON object.
                            parsed_obj = json.loads(obj_str)
                            objects.append(parsed_obj)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse an individual JSON object: {obj_str}")
                        start_index = -1
            
            return objects

        except Exception as e:
            logger.error(f"A critical error occurred during advanced JSON parsing: {e}")
            return []

    async def generate_quiz_simple(
        self,
        document_id: str,
        user_id: str,
        request: QuizGenerateRequest
    ) -> QuizModel:
        """Generate a quiz using the reliable flashcard-style generation"""
        try:
            document = await self.document_collection.find_one({"_id": ObjectId(document_id)})
            if not document:
                raise ValueError(f"Document {document_id} not found")

            content = document.get("content", "")
            if not content:
                raise ValueError("Document has no content")

            # Use the reliable AI model for quiz generation
            ai_client = together_ai
            
            system_prompt = """คุณคือผู้เชี่ยวชาญด้านการสร้างชุดคำถามปรนัย (Multiple Choice) คุณภาพสูงตามหลักการของ Bloom's Taxonomy
หน้าที่ของคุณคือสร้างคำถามจากเนื้อหาที่กำหนดให้ โดยต้องปฏิบัติตามข้อกำหนดต่อไปนี้อย่างเคร่งครัด:
1.  **รูปแบบผลลัพธ์ (Output Format)**: คุณต้องตอบกลับเป็น JSON array ที่สมบูรณ์แบบ (valid JSON array) เท่านั้น ห้ามมีข้อความอื่นใดๆ นอกเหนือจาก JSON array โดยเด็ดขาด
2.  **โครงสร้างคำถาม**: แต่ละคำถามใน array ต้องเป็น JSON object ที่มี key ดังต่อไปนี้: "question", "options", "correct_answer", "explanation", "bloom_level", "difficulty"
3.  **ตัวเลือก (Options)**: ต้องมี 4 ตัวเลือกเสมอ และต้องอยู่ในรูปแบบ array ของ string เช่น `["A) ตัวเลือก 1", "B) ตัวเลือก 2", "C) ตัวเลือก 3", "D) ตัวเลือก 4"]`
4.  **คำตอบที่ถูกต้อง (Correct Answer)**: ต้องเป็นเพียงตัวอักษรของตัวเลือกที่ถูกต้องเท่านั้น เช่น "A", "B", "C", หรือ "D"
5.  **ความหลากหลาย**: พยายามสร้างคำถามให้ครอบคลุมระดับต่างๆ ของ Bloom's Taxonomy ที่ระบุไว้ใน prompt
6.  **ความถูกต้อง**: เนื้อหาของคำถาม, ตัวเลือก, และคำอธิบาย ต้องถูกต้องตามเนื้อหาที่อ้างอิง"""
            
            prompt = f"""สร้างชุดคำถามปรนัยจำนวน {request.questionCount} ข้อจากเนื้อหาต่อไปนี้:

{content}

---
**ข้อกำหนดเพิ่มเติม:**
-   สร้างคำถามที่มีระดับความยาก: `{request.difficulty}`
-   ตรวจสอบให้แน่ใจว่าผลลัพธ์เป็น JSON array ที่สมบูรณ์เท่านั้น

**ตัวอย่างรูปแบบที่ต้องการ:**
```json
[
  {{
    "question": "ข้อใดคือเมืองหลวงของประเทศไทย?",
    "options": ["A) เชียงใหม่", "B) ภูเก็ต", "C) กรุงเทพมหานคร", "D) ขอนแก่น"],
    "correct_answer": "C",
    "explanation": "กรุงเทพมหานครเป็นเมืองหลวงของประเทศไทยตามที่ระบุไว้ในข้อมูลทั่วไป",
    "bloom_level": "remember",
    "difficulty": "easy"
  }},
  {{
    "question": "คำถามต่อไป...",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": "A",
    "explanation": "คำอธิบายสำหรับคำถามนี้",
    "bloom_level": "understand",
    "difficulty": "medium"
  }}
]
```"""

            # Generate questions with retry mechanism
            response = await ai_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=3000,
                retry_count=3,
                temperature=0.6
            )
            
            # Parse response
            questions = []
            total_points = 0
            
            try:
                # Use the new robust parser
                raw_questions = self._parse_llm_json_response(response)
                
                if not raw_questions:
                    raise ValueError("The robust parser could not extract any valid questions from the AI response.")
                
                for i, q in enumerate(raw_questions[:request.questionCount]):
                    if not isinstance(q, dict):
                        continue
                        
                    question_data = {
                        "questionId": str(uuid.uuid4()),
                        "question": q.get("question", f"Generated question {i+1}"),
                        "options": q.get("options", ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"]),
                        "correctAnswer": q.get("correct_answer", "A"),
                        "explanation": q.get("explanation", "Generated explanation"),
                        "bloomLevel": q.get("bloom_level", "remember"),
                        "difficulty": q.get("difficulty", request.difficulty),
                        "points": self._get_points_for_bloom_level(q.get("bloom_level", "remember"))
                    }
                    
                    question = QuizQuestion(**question_data)
                    questions.append(question)
                    total_points += question.points
                    
            except Exception as e:
                logger.error(f"Failed to parse quiz response: {e}")
                logger.debug(f"Raw response from AI: {response[:500]}...")
                # Generate fallback questions
                questions = self._generate_fallback_quiz(request.questionCount, request.difficulty)
                total_points = sum(q.points for q in questions)
                
            # Create quiz document for simple generation
            quiz_document = create_quiz_document(
                document_id=document_id,
                title=f"Quiz: {document.get('title', 'Untitled Document')}",
                description=f"Quiz generated from {document.get('title', 'document')}",
                questions=[q.dict() for q in questions],
                total_points=total_points,
                time_limit=request.timeLimit
            )
            
            result = await self.quiz_collection.insert_one(quiz_document)
            quiz_id = str(result.inserted_id)
            
            # Calculate actual bloom distribution from generated questions
            actual_bloom_distribution = {}
            for q in questions:
                level = q.bloomLevel
                actual_bloom_distribution[level] = actual_bloom_distribution.get(level, 0) + 1
            
            # Create response model
            quiz = QuizModel(
                quiz_id=quiz_id,
                document_id=document_id,
                title=quiz_document["title"],
                description=quiz_document["description"],
                questions=[q.dict() for q in questions],
                total_points=total_points,
                time_limit=request.timeLimit,
                bloom_distribution=actual_bloom_distribution
            )
            
            logger.info(f"Generated simple quiz {quiz_id} with {len(questions)} questions")
            return quiz

        except Exception as e:
            logger.error(f"Error generating simple quiz: {e}")
            raise ModelError(f"Failed to generate simple quiz: {str(e)}")


    async def generate_quiz(
        self,
        document_id: str,
        user_id: str,
        request: QuizGenerateRequest
    ) -> QuizModel:
        """Generate a quiz from document content using simple reliable approach"""
        try:
            document = await self.document_collection.find_one({"_id": ObjectId(document_id)})
            if not document:
                raise ValueError(f"Document {document_id} not found")

            content = document.get("content", "")
            if not content:
                raise ValueError("Document has no content")

            # Use simple quiz generation to avoid rate limits
            questions = []
            total_points = 0
            
            # Generate fallback questions if complex generation fails
            try:
                # Try simple generation first
                quiz = await self.generate_quiz_simple(document_id, user_id, request)
                return quiz
            except Exception as e:
                logger.warning(f"Simple generation failed, using fallback: {e}")
                questions = self._generate_fallback_quiz(request.questionCount, request.difficulty)
                total_points = sum(q.points for q in questions)

            # Create quiz document
            quiz_document = create_quiz_document(
                document_id=document_id,
                title=f"Quiz: {document.get('title', 'Untitled Document')}",
                description=f"Quiz generated from {document.get('title', 'document')}",
                questions=[q.dict() for q in questions],
                total_points=total_points,
                time_limit=request.timeLimit
            )
            
            result = await self.quiz_collection.insert_one(quiz_document)
            quiz_id = str(result.inserted_id)
            
            # Calculate actual bloom distribution from generated questions
            actual_bloom_distribution = {}
            for q in questions:
                level = q.bloomLevel
                actual_bloom_distribution[level] = actual_bloom_distribution.get(level, 0) + 1
            
            # Create response model
            quiz = QuizModel(
                quiz_id=quiz_id,
                document_id=document_id,
                title=quiz_document["title"],
                description=quiz_document["description"],
                questions=[q.dict() for q in questions],
                total_points=total_points,
                time_limit=request.timeLimit,
                bloom_distribution=actual_bloom_distribution
            )
            
            logger.info(f"Generated quiz {quiz_id} with {len(questions)} questions")
            return quiz

        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            raise ModelError(f"Failed to generate quiz: {str(e)}")
    
    def _generate_fallback_quiz(self, question_count: int, difficulty: str) -> List[QuizQuestion]:
        """Generate fallback quiz when AI generation fails"""
        questions = []
        bloom_levels = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
        
        for i in range(question_count):
            bloom_level = bloom_levels[i % len(bloom_levels)]
            
            question = QuizQuestion(
                questionId=str(uuid.uuid4()),
                question=f"คำถามตัวอย่างที่ {i+1} (ระดับ {bloom_level})",
                options=["A) ตัวเลือก 1", "B) ตัวเลือก 2", "C) ตัวเลือก 3", "D) ตัวเลือก 4"],
                correctAnswer="A",
                explanation=f"คำอธิบายสำหรับคำถามระดับ {bloom_level}",
                bloomLevel=bloom_level,
                difficulty=difficulty,
                points=self._get_points_for_bloom_level(bloom_level)
            )
            questions.append(question)
        
        return questions
    
    async def generate_quiz_with_explanations(
        self,
        document_id: str,
        user_id: str,
        request: QuizGenerateRequest
    ) -> QuizModel:
        """Generate quiz with enhanced explanations"""
        quiz = await self.generate_quiz(document_id, user_id, request)
        
        # Enhance explanations if requested
        if request.includeExplanations:
            try:
                document = await self.document_collection.find_one({"_id": ObjectId(document_id)})
                content = document.get("content", "")
                
                # Generate enhanced explanations for each question
                enhanced_questions = await self.advanced_generator.generate_explanations(
                    questions=[q.dict() for q in quiz.questions],
                    content=content
                )
                
                # Update quiz with enhanced explanations
                quiz.questions = [QuizQuestion(**q) for q in enhanced_questions]
                
                # Update in database
                await self.quiz_collection.update_one(
                    {"_id": ObjectId(quiz.quiz_id)},
                    {"$set": {"questions": enhanced_questions}}
                )
                
                logger.info(f"Enhanced explanations generated for quiz {quiz.quiz_id}")
                
            except Exception as e:
                logger.warning(f"Failed to enhance explanations: {e}")
        
        return quiz
    
    async def validate_quiz_quality(self, quiz_id: str) -> Dict[str, Any]:
        """Validate and assess quiz quality"""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            return {"error": "Quiz not found"}
        
        return await self.advanced_generator.validate_quiz_quality([q.dict() for q in quiz.questions])

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

        # Assuming 'attempts_allowed' is a field in your QuizModel, otherwise default to 1
        attempts_allowed = getattr(quiz, 'attempts_allowed', 1)

        attempts_count = await self.attempt_collection.count_documents({
            "quiz_id": quiz_id,
            "user_id": user_id
        })

        if attempts_allowed > 0 and attempts_count >= attempts_allowed:
            raise ValueError("Maximum attempts exceeded")

        results = self._calculate_results(quiz, submission)
        
        attempt_doc = {
            "attempt_id": str(uuid.uuid4()),
            "quiz_id": quiz_id,
            "user_id": user_id,
            "answers": submission.answers,
            "score": results["score"],
            "total_points": results["total_points"],
            "percentage": results["percentage"],
            "time_taken": submission.time_taken,
            "bloom_scores": results["bloom_scores"],
            "question_results": results["question_results"],
            "completed_at": datetime.now(timezone.utc)
        }


        attempt = QuizAttempt(**attempt_doc)

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

        # Handle answers as a list of strings in the same order as questions
        user_answers = submission.answers if isinstance(submission.answers, list) else []
        
        for i, question in enumerate(quiz.questions):
            user_answer = user_answers[i] if i < len(user_answers) else ""
            
            # Handle both dict and object formats
            if isinstance(question, dict):
                correct_answer = question.get("correctAnswer") or question.get("correct_answer", "")
                points = question.get("points", 1)
                bloom_level = question.get("bloomLevel") or question.get("bloom_level", "remember")
                question_id = question.get("questionId") or question.get("question_id", "")
                question_text = question.get("question", "")
                explanation = question.get("explanation", "")
            else:
                correct_answer = getattr(question, 'correctAnswer', "")
                points = getattr(question, 'points', 1)
                bloom_level = getattr(question, 'bloomLevel', "remember")
                question_id = getattr(question, 'questionId', "")
                question_text = getattr(question, 'question', "")
                explanation = getattr(question, 'explanation', "")
            
            is_correct = user_answer.strip().upper() == correct_answer.strip().upper()
            points_earned = points if is_correct else 0

            total_points += points
            earned_points += points_earned

            if bloom_level not in bloom_scores:
                bloom_scores[bloom_level] = 0
                bloom_totals[bloom_level] = 0
            
            bloom_scores[bloom_level] += points_earned
            bloom_totals[bloom_level] += points

            question_results.append({
                "question_id": question_id,
                "question": question_text,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "points_earned": points_earned,
                "points_possible": points,
                "bloom_level": bloom_level,
                "explanation": explanation
            })

        bloom_percentages = {}
        for level in bloom_scores:
            if bloom_totals.get(level, 0) > 0:
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
            quizzes = self.quiz_collection.find({"document_id": document_id})
            quiz_ids = [str(q["_id"]) async for q in quizzes]
            query["quiz_id"] = {"$in": quiz_ids}

        attempts = []
        async for attempt in self.attempt_collection.find(query).sort("completed_at", -1):
            quiz = await self.quiz_collection.find_one({"_id": ObjectId(attempt["quiz_id"])})
            attempt_data = {
                "attempt_id": attempt["attempt_id"],
                "quiz_id": attempt["quiz_id"],
                "quiz_title": quiz.get("title", "Unknown Quiz") if quiz else "Unknown Quiz",
                "score": attempt["score"],
                "total_points": attempt["total_points"],
                "percentage": attempt["percentage"],
                "time_taken": attempt["time_taken"],
                "completed_at": attempt["completed_at"].isoformat()
            }
            attempts.append(attempt_data)
        return attempts
    
    async def delete_quiz(self, quiz_id: str) -> bool:
        """Delete quiz and all associated attempts"""
        quiz_result = await self.quiz_collection.delete_one({"_id": ObjectId(quiz_id)})
        await self.attempt_collection.delete_many({"quiz_id": quiz_id})
        return quiz_result.deleted_count > 0

    async def get_quiz_results(self, attempt_id: str, user_id: str) -> Optional[QuizAttempt]:
        """Get specific quiz attempt results"""
        try:
            attempt_data = await self.attempt_collection.find_one({
                "attempt_id": attempt_id,
                "user_id": user_id
            })
            if attempt_data:
                return QuizAttempt(**attempt_data)
            return None
        except Exception as e:
            logger.error(f"Error getting quiz results: {e}")
            return None

    async def get_quiz_analytics(self, quiz_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a quiz"""
        try:
            # Get all attempts for this quiz
            attempts = []
            async for attempt in self.attempt_collection.find({"quiz_id": quiz_id}):
                attempts.append(attempt)
            
            if not attempts:
                return {
                    "total_attempts": 0,
                    "average_score": 0,
                    "completion_rate": 0,
                    "bloom_performance": {},
                    "difficulty_performance": {},
                    "time_analytics": {}
                }
            
            # Calculate analytics
            total_attempts = len(attempts)
            scores = [attempt["percentage"] for attempt in attempts]
            average_score = sum(scores) / len(scores) if scores else 0
            
            # Bloom's taxonomy performance
            bloom_performance = {}
            for attempt in attempts:
                for level, score in attempt.get("bloom_scores", {}).items():
                    if level not in bloom_performance:
                        bloom_performance[level] = []
                    bloom_performance[level].append(score)
            
            # Calculate averages for each bloom level
            bloom_averages = {}
            for level, scores in bloom_performance.items():
                bloom_averages[level] = sum(scores) / len(scores) if scores else 0
            
            # Time analytics
            times = [attempt["time_taken"] for attempt in attempts if "time_taken" in attempt]
            avg_time = sum(times) / len(times) if times else 0
            min_time = min(times) if times else 0
            max_time = max(times) if times else 0
            
            return {
                "total_attempts": total_attempts,
                "average_score": round(average_score, 2),
                "completion_rate": 100,  # All attempts are completed
                "bloom_performance": bloom_averages,
                "time_analytics": {
                    "average_time": round(avg_time, 2),
                    "min_time": min_time,
                    "max_time": max_time
                },
                "score_distribution": {
                    "excellent": len([s for s in scores if s >= 90]),
                    "good": len([s for s in scores if 70 <= s < 90]),
                    "fair": len([s for s in scores if 50 <= s < 70]),
                    "poor": len([s for s in scores if s < 50])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting quiz analytics: {e}")
            return {}

    async def get_user_topics(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all topics that have flashcards for a user"""
        try:
            # This would need to be implemented based on how topics are stored
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting user topics: {e}")
            return []

# quiz_generator = QuizGeneratorService()

def get_quiz_generator_service() -> QuizGeneratorService:
    """
    Dependency injector for the QuizGeneratorService.
    """
    return QuizGeneratorService()
