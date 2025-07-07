import asyncio
from typing import List, Dict, Any, Optional
import logging
from app.config import settings
from app.core.exceptions import ModelError

logger = logging.getLogger(__name__)

# Text correction using PyThaiNLP and English spell correction
def correct_text(text: str) -> str:
    """Correct text in both Thai and English"""
    if not text or not isinstance(text, str):
        return text
    
    # First apply English spell corrections for specific terms
    text = correct_english_terms(text)
    
    # Then apply Thai text correction if Thai characters are present
    if any('\u0e00' <= char <= '\u0e7f' for char in text):
        text = correct_thai_text(text)
    
    return text

async def grammar_check_with_llm(text: str, ai_client) -> str:
    """Use LLM to check and correct grammar"""
    if not text or not isinstance(text, str):
        return text
    
    system_prompt = """คุณเป็นผู้ช่วยตรวจสอบและแก้ไขไวยากรณ์ภาษาไทย
    ให้ตรวจสอบและแก้ไขข้อความที่ได้รับให้ถูกต้องตามหลักไวยากรณ์ภาษาไทย
    โดยเฉพาะ:
    - การใช้คำบุพบท (เช่น ใน, ที่, จาก, ตาม)
    - การใช้คำสันธาน (เช่น และ, หรือ, แต่, เพราะ)
    - การใช้คำขยาย (คำคุณศัพท์, คำกริยาวิเศษณ์)
    - การใช้เครื่องหมายวรรคตอน
    - การใช้คำที่เหมาะสมกับบริบท
    
    ให้ตอบเป็นข้อความที่แก้ไขแล้วเท่านั้น ไม่ต้องอธิบายการแก้ไข"""
    
    prompt = f"""กรุณาตรวจสอบและแก้ไขไวยากรณ์ของข้อความนี้:

{text}

ข้อความที่แก้ไขแล้ว:"""
    
    try:
        corrected = await ai_client.generate_response(prompt, system_prompt, max_tokens=512)
        return corrected.strip() if corrected else text
    except Exception as e:
        logger.error(f"Grammar check error: {e}")
        return text

def correct_english_terms(text: str) -> str:
    """Correct common English spelling mistakes for educational terms"""
    if not text or not isinstance(text, str):
        return text
    
    # Common misspellings and their corrections
    corrections = {
        # Flash card variations
        'flashcard': 'flash card',
        'flash-card': 'flash card',
        'flashcards': 'flash cards',
        'flash-cards': 'flash cards',
        'flascard': 'flash card',
        'flashcrd': 'flash card',
        'flaschcard': 'flash card',
        'flashkard': 'flash card',
        
        # Quiz variations
        'quizz': 'quiz',
        'quize': 'quiz',
        'kwiz': 'quiz',
        'quizzes': 'quizzes',  # This is correct
        'quizes': 'quizzes',
        'quizs': 'quizzes',
        'quis': 'quiz',
        'quiss': 'quiz',
    }
    
    # Case-insensitive replacement
    corrected_text = text
    for wrong, correct in corrections.items():
        # Replace whole words only (not parts of words)
        import re
        pattern = r'\b' + re.escape(wrong) + r'\b'
        corrected_text = re.sub(pattern, correct, corrected_text, flags=re.IGNORECASE)
    
    return corrected_text

def correct_thai_text(text: str) -> str:
    """Correct Thai text using PyThaiNLP"""
    if not text or not isinstance(text, str):
        return text
        
    try:
        from pythainlp.spell import correct
        from pythainlp.util import normalize
        
        # Only process Thai text (contains Thai characters)
        if not any('\u0e00' <= char <= '\u0e7f' for char in text):
            return text
            
        # Normalize and correct the text
        normalized = normalize(text)
        corrected = correct(normalized)
        return corrected if corrected else text
    except ImportError:
        logger.warning("PyThaiNLP not installed, skipping Thai text correction")
        return text
    except Exception as e:
        logger.error(f"Error correcting Thai text '{text[:50]}...': {str(e)}")
        return text

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
        temperature: Optional[float] = None,
        retry_count: int = 3
    ) -> str:
        """Generate response using Together AI with token management and rate limiting"""
        if not self.client:
            # Return a mock response if Together AI is not available
            return f"Mock AI response to: {prompt[:100]}..."
        
        # Ensure we stay within token limits
        max_input_tokens = 6000  # Conservative limit to leave room for response
        truncated_prompt = prompt[:max_input_tokens] if len(prompt) > max_input_tokens else prompt
        truncated_system = system_prompt[:1000] if system_prompt and len(system_prompt) > 1000 else system_prompt
        
        # Reduce max_tokens to stay under API limit
        safe_max_tokens = min(max_tokens or self.max_tokens, 1500)
            
        for attempt in range(retry_count):
            try:
                messages = []
                if truncated_system:
                    messages.append({"role": "system", "content": truncated_system})
                messages.append({"role": "user", "content": truncated_prompt})

                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    max_tokens=safe_max_tokens,
                    temperature=temperature or self.temperature
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Together AI API error (attempt {attempt + 1}): {error_msg}")
                
                # Handle rate limiting with exponential backoff
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < retry_count - 1:
                        wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                        logger.info(f"Rate limited, waiting {wait_time} seconds before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                
                # Handle token limit errors
                if "token" in error_msg.lower() and "limit" in error_msg.lower():
                    if attempt < retry_count - 1 and len(truncated_prompt) > 1000:
                        # Further reduce prompt size
                        truncated_prompt = truncated_prompt[:len(truncated_prompt)//2]
                        safe_max_tokens = min(safe_max_tokens, 1000)
                        logger.info(f"Token limit exceeded, reducing prompt size to {len(truncated_prompt)} chars")
                        continue
                
                # If last attempt or non-recoverable error
                if attempt == retry_count - 1:
                    logger.error(f"All retry attempts failed. Last error: {error_msg}")
                    return f"AI service temporarily unavailable. Error: {error_msg[:100]}..."
                
                # Wait before next attempt for other errors
                await asyncio.sleep(2 ** attempt)

    def chunk_content(self, content: str, max_chunk_length: int = 2000) -> List[str]:
        """Split content into chunks that fit within token limits"""
        # Conservative chunking - roughly 4 chars per token, so 2000 chars ≈ 500 tokens
        # This leaves room for prompts and responses within 8193 limit
        words = content.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > max_chunk_length and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    async def generate_flashcards(self, content: str, count: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards from content with chunking for large documents"""
        system_prompt = """คุณเป็นผู้ช่วยสร้างบัตรคำศัพท์ (flash cards) ที่ช่วยในการเรียนรู้ 
        สร้างคำถามและคำตอบที่มีคุณภาพสูงจากเนื้อหาที่ให้มา โดยใช้ไวยากรณ์ภาษาไทยที่ถูกต้อง
        ให้ตอบในรูปแบบ JSON array ที่มี objects ที่มี fields: question, answer, difficulty
        difficulty ให้เป็น easy, medium, หรือ hard
        
        สำคัญ - ตรวจสอบไวยากรณ์ภาษาไทยให้ถูกต้อง:
        - ใช้คำศัพท์ที่ถูกต้อง (เช่น "กล้ามเนื้อ" ไม่ใช่ "กลามเนอ", "ข้อต่อแบบลูกกลมในเบ้า" ไม่ใช่ "ขอตอแบบลกกลมในเบา")
        - ใช้คำบุพบท คำสันธาน ให้เหมาะสมกับบริบท
        - ใช้เครื่องหมายวรรคตอนให้ถูกต้อง
        - ใช้การเชื่อมประโยคที่เป็นธรรมชาติ
        - ตรวจสอบการสะกดคำให้ถูกต้อง
        - ใช้ "flash cards" (แยกเป็น 2 คำ) ไม่ใช่ "flashcards"
        - ใช้ "quiz" หรือ "quizzes" (สะกดให้ถูกต้อง)
        
        คำศัพท์ทางวิทยาศาสตร์ที่ต้องใช้ให้ถูกต้อง:
        - ข้อต่อแบบลูกกลมในเบ้า (ball and socket joint) - เคลื่อนไหวได้หลายทิศทาง
        - ข้อต่อแบบบานพับ (hinge joint) - เคลื่อนไหวได้ทิศทางเดียว
        - ข้อต่อแบบหมุน (pivot joint) - หมุนรอบแกน
        - กล้ามเนื้อ (muscle) - เนื้อเยื่อที่หดตัวได้
        - เส้นใยกล้ามเนื้อ (muscle fiber) - เซลล์กล้ามเนื้อ
        - เส้นเอ็น (tendon) - เชื่อมกล้ามเนื้อกับกระดูก
        - เอ็นยึด (ligament) - เชื่อมกระดูกกับกระดูก
        - กระดูกอ่อน (cartilage) - เนื้อเยื่อยืดหยุ่น
        
        หลักการสร้างคำถาม:
        - คำถามต้องชัดเจน เข้าใจง่าย
        - คำตอบต้องตรงประเด็นและถูกต้องทางวิทยาศาสตร์
        - ใช้คำศัพท์ทางวิทยาศาสตร์ที่ถูกต้อง
        - หลีกเลี่ยงคำที่กำกวมหรือใช้ยาก
        - ให้ตัวอย่างที่เป็นรูปธรรม"""
        
        all_flashcards = []
        
        # Check if content is too long and needs chunking
        if len(content) > 2000:  # Conservative chunking for token limits
            chunks = self.chunk_content(content, 2000)
            cards_per_chunk = max(1, count // len(chunks))
            
            for i, chunk in enumerate(chunks):
                # Calculate how many cards to generate from this chunk
                remaining_cards = count - len(all_flashcards)
                if remaining_cards <= 0:
                    break
                    
                chunk_cards = min(cards_per_chunk, remaining_cards)
                if i == len(chunks) - 1:  # Last chunk gets any remaining cards
                    chunk_cards = remaining_cards
                
                prompt = f"""สร้าง flash cards {chunk_cards} ใบจากเนื้อหาต่อไปนี้:

{chunk}

ให้ตอบในรูปแบบ JSON array เท่านั้น:
[
  {{
    "question": "คำถาม",
    "answer": "คำตอบ",
    "difficulty": "medium"
  }}
]"""

                try:
                    response = await self.generate_response(prompt, system_prompt, max_tokens=1024, retry_count=3)
                    import json
                    
                    try:
                        flashcards = json.loads(response)
                        all_flashcards.extend(flashcards[:chunk_cards])
                    except json.JSONDecodeError:
                        logger.warning(f"JSON parsing failed for chunk {i+1}, skipping")
                        continue
                        
                except Exception as e:
                    logger.error(f"Error generating flashcards for chunk {i+1}: {e}")
                    continue
        else:
            # Content is small enough, process normally
            prompt = f"""สร้าง flash cards {count} ใบจากเนื้อหาต่อไปนี้:

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
                response = await self.generate_response(prompt, system_prompt, max_tokens=1500, retry_count=3)
                import json
                
                try:
                    flashcards = json.loads(response)
                    all_flashcards.extend(flashcards)
                except json.JSONDecodeError:
                    # Fallback: create mock flashcards if JSON parsing fails
                    all_flashcards = [
                        {
                            "question": f"คำถามที่ {i+1} จากเนื้อหา",
                            "answer": f"คำตอบตัวอย่างที่ {i+1}",
                            "difficulty": "medium"
                        }
                        for i in range(min(count, 3))
                    ]
                    
            except Exception as e:
                logger.error(f"Flashcard generation error: {e}")
                # Return mock flashcards as fallback
                all_flashcards = [
                    {
                        "question": f"คำถามตัวอย่างที่ {i+1}",
                        "answer": f"คำตอบตัวอย่างที่ {i+1}",
                        "difficulty": "medium"
                    }
                    for i in range(min(count, 3))
                ]
        
        # Ensure we don't exceed requested count and have at least some cards
        result = all_flashcards[:count] if all_flashcards else [
            {
                "question": f"คำถามตัวอย่างที่ {i+1}",
                "answer": f"คำตอบตัวอย่างที่ {i+1}",
                "difficulty": "medium"
            }
            for i in range(min(count, 3))
        ]
        
        return result

    async def generate_flashcards_from_prompt(self, prompt: str, count: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards from a custom prompt"""
        system_prompt = """คุณเป็นผู้ช่วยสร้างบัตรคำศัพท์ (flash cards) ที่ช่วยในการเรียนรู้ 
        สร้างคำถามและคำตอบที่มีคุณภาพสูงตามที่ร้องขอ โดยใช้ไวยากรณ์ภาษาไทยที่ถูกต้อง
        ให้ตอบในรูปแบบ JSON array ที่มี objects ที่มี fields: question, answer, difficulty
        difficulty ให้เป็น easy, medium, หรือ hard
        
        สำคัญ - ตรวจสอบไวยากรณ์ภาษาไทยให้ถูกต้อง:
        - ใช้คำศัพท์ที่ถูกต้อง (เช่น "กล้ามเนื้อ" ไม่ใช่ "กลามเนอ", "ข้อต่อแบบลูกกลมในเบ้า" ไม่ใช่ "ขอตอแบบลกกลมในเบา")
        - ใช้คำบุพบท คำสันธาน ให้เหมาะสมกับบริบท
        - ใช้เครื่องหมายวรรคตอนให้ถูกต้อง
        - ใช้การเชื่อมประโยคที่เป็นธรรมชาติ
        - ตรวจสอบการสะกดคำให้ถูกต้อง
        - ใช้ "flash cards" (แยกเป็น 2 คำ) ไม่ใช่ "flashcards"
        - ใช้ "quiz" หรือ "quizzes" (สะกดให้ถูกต้อง)
        
        คำศัพท์ทางวิทยาศาสตร์ที่ต้องใช้ให้ถูกต้อง:
        - ข้อต่อแบบลูกกลมในเบ้า (ball and socket joint) - เคลื่อนไหวได้หลายทิศทาง
        - ข้อต่อแบบบานพับ (hinge joint) - เคลื่อนไหวได้ทิศทางเดียว
        - ข้อต่อแบบหมุน (pivot joint) - หมุนรอบแกน
        - กล้ามเนื้อ (muscle) - เนื้อเยื่อที่หดตัวได้
        - เส้นใยกล้ามเนื้อ (muscle fiber) - เซลล์กล้ามเนื้อ
        - เส้นเอ็น (tendon) - เชื่อมกล้ามเนื้อกับกระดูก
        - เอ็นยึด (ligament) - เชื่อมกระดูกกับกระดูก
        - กระดูกอ่อน (cartilage) - เนื้อเยื่อยืดหยุ่น
        
        หลักการสร้างคำถาม:
        - คำถามต้องชัดเจน เข้าใจง่าย
        - คำตอบต้องตรงประเด็นและถูกต้องทางวิทยาศาสตร์
        - ใช้คำศัพท์ทางวิทยาศาสตร์ที่ถูกต้อง
        - หลีกเลี่ยงคำที่กำกวมหรือใช้ยาก
        - ให้ตัวอย่างที่เป็นรูปธรรม"""
        
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
            response = await self.generate_response(formatted_prompt, system_prompt, max_tokens=1500, retry_count=3)
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
        
        system_prompt = """คุณเป็นผู้ช่วยสร้างข้อสอบ (quiz) ที่ใช้หลัก Bloom's Taxonomy
        สร้างคำถามแบบปรนัยที่มีคุณภาพสูงจากเนื้อหาที่ให้มา โดยใช้ไวยากรณ์ภาษาไทยที่ถูกต้อง
        แต่ละคำถามต้องมี 4 ตัวเลือก (A, B, C, D) และคำอธิบายคำตอบที่ถูกต้อง
        
        ระดับ Bloom's Taxonomy:
        - remember (จำ): ข้อเท็จจริง คำนิยาม
        - understand (เข้าใจ): อธิบาย สรุป ตีความ
        - apply (ประยุกต์): ใช้ความรู้ในสถานการณ์ใหม่
        - analyze (วิเคราะห์): แยกแยะ เปรียบเทียบ
        - evaluate (ประเมิน): ตัดสิน วิจารณ์
        - create (สร้างสรรค์): สร้าง ออกแบบ วางแผน
        
        สำคัญ - ตรวจสอบไวยากรณ์ภาษาไทยให้ถูกต้อง:
        - ใช้คำศัพท์ที่ถูกต้อง (เช่น "กล้ามเนื้อ" ไม่ใช่ "กลามเนอ")
        - ใช้คำบุพบท คำสันธาน ให้เหมาะสมกับบริบท
        - ใช้เครื่องหมายวรรคตอนให้ถูกต้อง
        - ใช้การเชื่อมประโยคที่เป็นธรรมชาติ
        - ตรวจสอบการสะกดคำให้ถูกต้อง
        - ใช้ "flash cards" (แยกเป็น 2 คำ) ไม่ใช่ "flashcards"
        - ใช้ "quiz" หรือ "quizzes" (สะกดให้ถูกต้อง)
        
        หลักการสร้างคำถาม:
        - คำถามต้องชัดเจน เข้าใจง่าย
        - ตัวเลือกต้องสมเหตุสมผล ไม่ชัดเจนเกินไป
        - คำอธิบายต้องให้เหตุผลที่ถูกต้อง
        - หลีกเลี่ยงคำที่กำกวมหรือใช้ยาก"""

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

        return await self.generate_response(prompt, system_prompt, max_tokens=1000, retry_count=3)

# Global instance
together_ai = TogetherAIClient()
