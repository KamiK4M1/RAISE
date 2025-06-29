import asyncio
from typing import List, Dict, Any, Optional
import logging
from together import Together
from app.config import settings
from app.core.exceptions import ModelError

logger = logging.getLogger(__name__)

class TogetherAIClient:
    def __init__(self):
        if not settings.together_ai_api_key:
            raise ModelError("Together AI API key not configured")
        
        self.client = Together(api_key=settings.together_ai_api_key)
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
            raise ModelError(f"การเรียกใช้โมเดล AI ล้มเหลว: {str(e)}")

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
            flashcards = json.loads(response)
            return flashcards[:count]  # Ensure we don't exceed requested count
            
        except json.JSONDecodeError:
            logger.error("Failed to parse flashcard JSON response")
            raise ModelError("ไม่สามารถสร้างบัตรคำศัพท์ได้")
        except Exception as e:
            logger.error(f"Flashcard generation error: {e}")
            raise ModelError(f"เกิดข้อผิดพลาดในการสร้างบัตรคำศัพท์: {str(e)}")

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

                try:
                    response = await self.generate_response(prompt, system_prompt)
                    import json
                    questions = json.loads(response)
                    all_questions.extend(questions)
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