import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ThaiTextProcessor:
    def __init__(self):
        # Thai text patterns
        self.thai_pattern = re.compile(r'[\u0E00-\u0E7F]+')
        self.english_pattern = re.compile(r'[a-zA-Z]+')
        
        # Common Thai stop words
        self.thai_stopwords = {
            'และ', 'หรือ', 'แต่', 'ใน', 'บน', 'จาก', 'ไป', 'มา', 'ที่', 'ซึ่ง', 'อัน', 'นั้น', 'นี้',
            'เป็น', 'คือ', 'มี', 'ได้', 'จะ', 'แล้ว', 'ก็', 'ให้', 'กับ', 'ของ', 'ตาม', 'โดย', 'เพื่อ',
            'ถ้า', 'เมื่อ', 'แม้', 'แต่ง', 'อย่าง', 'เช่น', 'คล้าย', 'เหมือน', 'ทั้งหมด', 'ทุก', 'แต่ละ',
            'เอง', 'กัน', 'บ้าง', 'ละ', 'นะ', 'ค่ะ', 'ครับ', 'จ้า', 'เนอะ', 'เหรอ', 'ไหม', 'มั้ย'
        }

    def is_thai_text(self, text: str) -> bool:
        """Check if text contains Thai characters"""
        return bool(self.thai_pattern.search(text))

    def extract_thai_words(self, text: str) -> List[str]:
        """Extract Thai words from text"""
        try:
            # Simple word extraction based on spaces and punctuation
            # For production, consider using PyThaiNLP for better tokenization
            words = re.findall(r'[\u0E00-\u0E7F]+', text)
            return [word for word in words if len(word) > 1]
        except Exception as e:
            logger.error(f"Error extracting Thai words: {e}")
            return []

    def clean_thai_text(self, text: str) -> str:
        """Clean and normalize Thai text"""
        try:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove common punctuation but keep Thai punctuation
            text = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s\.\?\!\,\:\;\-\(\)\[\]\{\}\"\'\/\\\@\#\$\%\^\&\*\+\=\_\~\`\|\<\>]', '', text)
            
            # Normalize spaces around punctuation
            text = re.sub(r'\s*([\.!\?,:;])\s*', r'\1 ', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning Thai text: {e}")
            return text

    def remove_stopwords(self, words: List[str]) -> List[str]:
        """Remove Thai stopwords from word list"""
        return [word for word in words if word.lower() not in self.thai_stopwords]

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from Thai text"""
        try:
            # Clean text
            cleaned_text = self.clean_thai_text(text)
            
            # Extract words
            words = self.extract_thai_words(cleaned_text)
            
            # Remove stopwords
            keywords = self.remove_stopwords(words)
            
            # Count frequency
            word_freq = {}
            for word in keywords:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # Return top keywords
            return [word for word, freq in sorted_words[:max_keywords]]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []

    def detect_language(self, text: str) -> str:
        """Detect if text is primarily Thai or English"""
        thai_chars = len(self.thai_pattern.findall(text))
        english_chars = len(self.english_pattern.findall(text))
        
        if thai_chars > english_chars:
            return "thai"
        elif english_chars > thai_chars:
            return "english"
        else:
            return "mixed"

    def segment_sentences(self, text: str) -> List[str]:
        """Simple sentence segmentation for Thai text"""
        try:
            # Split by common sentence endings
            sentences = re.split(r'[\.!\?]+', text)
            
            # Clean and filter empty sentences
            sentences = [s.strip() for s in sentences if s.strip()]
            
            return sentences
            
        except Exception as e:
            logger.error(f"Error segmenting sentences: {e}")
            return [text]

    def format_for_display(self, text: str) -> str:
        """Format Thai text for better display"""
        try:
            # Clean text
            formatted_text = self.clean_thai_text(text)
            
            # Ensure proper spacing
            formatted_text = re.sub(r'(\u0E00-\u0E7F)([a-zA-Z])', r'\1 \2', formatted_text)
            formatted_text = re.sub(r'([a-zA-Z])(\u0E00-\u0E7F)', r'\1 \2', formatted_text)
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting text: {e}")
            return text

    def count_thai_characters(self, text: str) -> int:
        """Count Thai characters in text"""
        return len(self.thai_pattern.findall(text))

    def count_words(self, text: str) -> int:
        """Estimate word count for Thai text"""
        # Simple estimation based on spaces and Thai character groups
        thai_words = len(self.extract_thai_words(text))
        english_words = len(self.english_pattern.findall(text))
        return thai_words + english_words

# Global instance
thai_processor = ThaiTextProcessor()