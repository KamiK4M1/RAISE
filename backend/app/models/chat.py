"""
Chat and RAG Models for RAISE Learning Platform
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """Chat message model"""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[str] = None
    user_id: str
    document_id: str
    session_id: Optional[str] = None
    question: str
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    """Request for asking a question"""
    question: str
    document_id: str
    session_id: Optional[str] = None
    use_chat_history: bool = True
    max_context_chunks: int = 5

class ChatSource(BaseModel):
    """Source information for chat response"""
    chunk_id: str
    text: str
    similarity: float

class ChatResponse(BaseModel):
    """Response from chat/RAG system"""
    answer: str
    sources: List[ChatSource]
    confidence: float
    session_id: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    """Chat history response"""
    messages: List[ChatMessage]
    total_messages: int
    session_id: Optional[str] = None