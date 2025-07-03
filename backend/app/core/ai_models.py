import asyncio
from typing import List, Dict, Any, Optional
import logging
from app.config import settings
from app.core.exceptions import ModelError

logger = logging.getLogger(__name__)

class TogetherAIClient:
    def __init__(self):
        if not settings.together_ai_api_key:
            raise ModelError("Together AI API key not configured")
        
        # Import Together AI here to avoid import issues
        try:
            from together import Together
            self.client = Together(api_key=settings.together_ai_api_key)
        except ImportError:
            logger.warning("Together AI package not installed. Some features may not work.")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Together AI client: {e}")
            self.client = None
            
        self.model = settings.llm_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using Together AI"""
        if not self.client:
            # Return a mock response if Together AI is not available
            return f"Mock AI response to: {prompt[:100]}..."
            
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Together AI API error: {e}")
            # Return a fallback response instead of raising an error
            return f"AI service temporarily unavailable. Echo: {prompt[:200]}..."

    async def generate_flashcards(self, content: str, count: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards from content"""
        system_prompt = """คุณเป็นผู้ช่วยสร้างบัตรคำศัพท์ (flashcards) ที่ช่วยในการเรียนรู้ 
        สร้างคำถามและคำตอบที่มีคุณภาพสูงจากเนื้อหาที่ให้มา
        ให้ตอบในรูปแบบ JSON array ที่มี objects ที่มี fields: question, answer, difficulty
        difficulty ให้เป็น easy, medium, หรือ hard
        ใช้ภาษาไทยในการสร้างคำถามและคำตอบ"""
        
        prompt = f"""สร้างบัตรคำศัพท์ {count} ใบจากเนื้อหาต่อไปนี้:

{content}

ให้ตอบในรูปแบบ JSON array เท่านั้น:
[
  {{
    "question": "คำถาม",
    "answer": "คำตอบ",
    "difficulty": "medium"
  }}
]"""

        try:
            response = await self.generate_response(prompt, system_prompt)
            # Parse JSON response
            import json
            
            # Try to extract JSON from response
            try:
                flashcards = json.loads(response)
            except json.JSONDecodeError:
                # Fallback: create mock flashcards if JSON parsing fails
                flashcards = [
                    {
                        "question": f"คำถามที่ {i+1} จากเนื้อหา",
                        "answer": f"คำตอบตัวอย่างที่ {i+1}",
                        "difficulty": "medium"
                    }
                    for i in range(min(count, 3))
                ]
                
            return flashcards[:count]  # Ensure we don't exceed requested count
            
        except Exception as e:
            logger.error(f"Flashcard generation error: {e}")
            # Return mock flashcards as fallback
            return [
                {
                    "question": f"คำถามตัวอย่างที่ {i+1}",
                    "answer": f"คำตอบตัวอย่างที่ {i+1}",
                    "difficulty": "medium"
                }
                for i in range(min(count, 3))
            ]

    async def generate_flashcards_from_prompt(self, prompt: str, count: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards from a custom prompt"""
        system_prompt = """คุณเป็นผู้ช่วยสร้างบัตรคำศัพท์ (flashcards) ที่ช่วยในการเรียนรู้ 
        สร้างคำถามและคำตอบที่มีคุณภาพสูงตามที่ร้องขอ
        ให้ตอบในรูปแบบ JSON array ที่มี objects ที่มี fields: question, answer, difficulty
        difficulty ให้เป็น easy, medium, หรือ hard
        ใช้ภาษาไทยในการสร้างคำถามและคำตอบ"""
        
        formatted_prompt = f"""{prompt}

ให้ตอบในรูปแบบ JSON array เท่านั้น:
[
  {{
    "question": "คำถาม",
    "answer": "คำตอบ",
    "difficulty": "medium"
  }}
]"""

        try:
            response = await self.generate_response(formatted_prompt, system_prompt)
            # Parse JSON response
            import json
            
            # Try to extract JSON from response
            try:
                flashcards = json.loads(response)
            except json.JSONDecodeError:
                # Fallback: create mock flashcards if JSON parsing fails
                flashcards = [
                    {
                        "question": f"คำถามที่ {i+1} จากหัวข้อ",
                        "answer": f"คำตอบตัวอย่างที่ {i+1}",
                        "difficulty": "medium"
                    }
                    for i in range(min(count, 3))
                ]
                
            return flashcards[:count]  # Ensure we don't exceed requested count
            
        except Exception as e:
            logger.error(f"Flashcard generation from prompt error: {e}")
            # Return mock flashcards as fallback
            return [
                {
                    "question": f"คำถามตัวอย่างที่ {i+1}",
                    "answer": f"คำตอบตัวอย่างที่ {i+1}",
                    "difficulty": "medium"
                }
                for i in range(min(count, 3))
            ]

    async def generate_quiz_questions(
        self, 
        content: str, 
        count: int = 10,
        bloom_distribution: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions based on Bloom's taxonomy"""
        
        default_distribution = {
            "remember": 2,
            "understand": 2,
            "apply": 2,
            "analyze": 2,
            "evaluate": 1,
            "create": 1
        }
        
        distribution = bloom_distribution or default_distribution
        
        system_prompt = """คุณเป็นผู้ช่วยสร้างข้อสอบที่ใช้หลัก Bloom's Taxonomy
        สร้างคำถามแบบปรนัยที่มีคุณภาพสูงจากเนื้อหาที่ให้มา
        แต่ละคำถามต้องมี 4 ตัวเลือก (A, B, C, D) และคำอธิบายคำตอบที่ถูกต้อง
        
        ระดับ Bloom's Taxonomy:
        - remember (จำ): ข้อเท็จจริง คำนิยาม
        - understand (เข้าใจ): อธิบาย สรุป ตีความ
        - apply (ประยุกต์): ใช้ความรู้ในสถานการณ์ใหม่
        - analyze (วิเคราะห์): แยกแยะ เปรียบเทียบ
        - evaluate (ประเมิน): ตัดสิน วิจารณ์
        - create (สร้างสรรค์): สร้าง ออกแบบ วางแผน"""

        all_questions = []
        
        for bloom_level, question_count in distribution.items():
            if question_count > 0:
                try:
                    prompt = f"""สร้างคำถามระดับ {bloom_level} จำนวน {question_count} ข้อ จากเนื้อหาต่อไปนี้:

{content}

ให้ตอบในรูปแบบ JSON array:
[
  {{
    "question": "คำถาม",
    "options": ["A) ตัวเลือก 1", "B) ตัวเลือก 2", "C) ตัวเลือก 3", "D) ตัวเลือก 4"],
    "correct_answer": "A",
    "explanation": "คำอธิบาย",
    "bloom_level": "{bloom_level}",
    "difficulty": "medium"
  }}
]"""

                    response = await self.generate_response(prompt, system_prompt)
                    import json
                    
                    try:
                        questions = json.loads(response)
                        all_questions.extend(questions)
                    except json.JSONDecodeError:
                        # Fallback mock questions
                        mock_questions = [
                            {
                                "question": f"คำถามตัวอย่าง {bloom_level} ที่ {i+1}",
                                "options": ["A) ตัวเลือก 1", "B) ตัวเลือก 2", "C) ตัวเลือก 3", "D) ตัวเลือก 4"],
                                "correct_answer": "A",
                                "explanation": f"คำอธิบายสำหรับคำถาม {bloom_level}",
                                "bloom_level": bloom_level,
                                "difficulty": "medium"
                            }
                            for i in range(question_count)
                        ]
                        all_questions.extend(mock_questions)
                        
                except Exception as e:
                    logger.error(f"Error generating {bloom_level} questions: {e}")
                    continue

        return all_questions[:count]

    async def answer_question(self, question: str, context: str) -> str:
        """Answer a question based on given context"""
        system_prompt = """คุณเป็นผู้ช่วยตอบคำถามที่ใช้เนื้อหาจากเอกสารเป็นฐาน
        ตอบคำถามโดยอ้างอิงเนื้อหาที่ให้มา และระบุแหล่งที่มาอย่างชัดเจน
        หากไม่มีข้อมูลเพียงพอในเนื้อหาที่ให้มา ให้บอกว่าไม่มีข้อมูลเพียงพอ
        ใช้ภาษาไทยในการตอบ"""

        prompt = f"""เนื้อหาอ้างอิง:
{context}

คำถาม: {question}

กรุณาตอบคำถามโดยอ้างอิงจากเนื้อหาข้างต้น:"""

        return await self.generate_response(prompt, system_prompt)

# Global instance
together_ai = TogetherAIClient()
