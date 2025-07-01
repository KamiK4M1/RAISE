"""
RAG (Retrieval Augmented Generation) Service for RAISE Learning Platform

This service handles:
- Document retrieval using vector similarity
- Context generation for AI responses
- Chat history management
- Source attribution and confidence scoring
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
from bson import ObjectId

from app.database.mongodb import (
    mongodb_manager, Collections,
    create_chat_message_document
)
from app.core.vector_search import similarity_search
from app.core.embeddings import get_embeddings
from app.core.ai_models import get_completion
from app.models.chat import ChatMessage, ChatRequest, ChatResponse
from app.services.document_service import document_service

logger = logging.getLogger(__name__)

class RAGService:
    """Service for RAG-based question answering using MongoDB"""

    def __init__(self):
        self.chat_collection = mongodb_manager.get_chat_messages_collection()
        self.documents_collection = mongodb_manager.get_documents_collection()
        self.chunks_collection = mongodb_manager.get_document_chunks_collection()

    async def ask_question(
        self,
        user_id: str,
        document_id: str,
        question: str,
        session_id: Optional[str] = None,
        use_chat_history: bool = True,
        max_context_chunks: int = 5
    ) -> ChatResponse:
        """
        Answer a question using RAG with document context
        
        Args:
            user_id: User ID
            document_id: Document ID to search in
            question: User's question
            session_id: Optional chat session ID
            use_chat_history: Whether to include chat history in context
            max_context_chunks: Maximum number of context chunks to use
            
        Returns:
            ChatResponse with answer, sources, and confidence
        """
        try:
            # Verify document access
            document = await document_service.get_document_by_id(document_id, user_id)
            
            # Get question embedding
            question_embedding = await get_embeddings([question])
            if not question_embedding:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate question embedding"
                )
            
            # Retrieve relevant chunks
            similar_chunks = await similarity_search(
                query_embedding=question_embedding[0],
                document_id=document_id,
                limit=max_context_chunks,
                min_similarity=0.7
            )
            
            if not similar_chunks:
                return ChatResponse(
                    answer="I couldn't find relevant information in the document to answer your question.",
                    sources=[],
                    confidence=0.0,
                    session_id=session_id
                )
            
            # Build context from chunks
            context_parts = []
            sources = []
            
            for chunk in similar_chunks:
                context_parts.append(f"Context {len(context_parts) + 1}: {chunk['text']}")
                sources.append({
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                    "similarity": chunk["similarity"]
                })
            
            context = "\n\n".join(context_parts)
            
            # Get chat history if requested
            chat_history = []
            if use_chat_history and session_id:
                chat_history = await self.get_chat_history(user_id, document_id, session_id, limit=5)
            
            # Generate answer using AI
            answer, confidence = await self._generate_answer(
                question=question,
                context=context,
                chat_history=chat_history,
                document_title=document.title
            )
            
            # Save chat message
            await self._save_chat_message(
                user_id=user_id,
                document_id=document_id,
                question=question,
                answer=answer,
                sources=sources,
                confidence=confidence,
                session_id=session_id
            )
            
            return ChatResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                session_id=session_id
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in RAG question answering: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing question"
            )

    async def _generate_answer(
        self,
        question: str,
        context: str,
        chat_history: List[Dict[str, Any]],
        document_title: str
    ) -> Tuple[str, float]:
        """Generate answer using AI model with context"""
        try:
            # Build chat history context
            history_context = ""
            if chat_history:
                history_parts = []
                for msg in chat_history[-3:]:  # Last 3 messages
                    history_parts.append(f"Q: {msg['question']}\nA: {msg['answer']}")
                history_context = f"\n\nPrevious conversation:\n" + "\n\n".join(history_parts)
            
            # Create prompt
            prompt = f"""You are an AI assistant helping a student understand the document "{document_title}". 
Answer the question based on the provided context. Be accurate, helpful, and cite specific information from the context when possible.

Context from document:
{context}{history_context}

Question: {question}

Instructions:
1. Answer based primarily on the provided context
2. If the context doesn't contain enough information, say so clearly
3. Be concise but comprehensive
4. Use a helpful, educational tone
5. If relevant, reference specific parts of the context

Answer:"""

            # Get AI response
            answer = await get_completion(prompt)
            
            # Calculate confidence based on context relevance
            confidence = self._calculate_confidence(question, context, answer)
            
            return answer, confidence

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "I'm sorry, I couldn't generate an answer to your question.", 0.0

    def _calculate_confidence(self, question: str, context: str, answer: str) -> float:
        """Calculate confidence score for the answer"""
        try:
            # Simple heuristic-based confidence calculation
            confidence = 0.5  # Base confidence
            
            # Increase confidence if answer is longer (more detailed)
            if len(answer) > 100:
                confidence += 0.1
            
            # Increase confidence if answer references context
            context_keywords = set(context.lower().split())
            answer_keywords = set(answer.lower().split())
            overlap = len(context_keywords.intersection(answer_keywords))
            
            if overlap > 5:
                confidence += 0.2
            elif overlap > 2:
                confidence += 0.1
            
            # Decrease confidence for uncertain language
            uncertain_phrases = ["i don't know", "unclear", "not sure", "might be", "possibly"]
            if any(phrase in answer.lower() for phrase in uncertain_phrases):
                confidence -= 0.2
            
            # Clamp between 0 and 1
            return max(0.0, min(1.0, confidence))
            
        except Exception:
            return 0.5

    async def _save_chat_message(
        self,
        user_id: str,
        document_id: str,
        question: str,
        answer: str,
        sources: List[Dict[str, Any]],
        confidence: float,
        session_id: Optional[str]
    ):
        """Save chat message to database"""
        try:
            chat_document = create_chat_message_document(
                user_id=user_id,
                document_id=document_id,
                question=question,
                answer=answer,
                session_id=session_id,
                sources=sources,
                confidence=confidence
            )
            
            await self.chat_collection.insert_one(chat_document)
            
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")

    async def get_chat_history(
        self,
        user_id: str,
        document_id: str,
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get chat history for a user and document"""
        try:
            filter_query = {
                "user_id": ObjectId(user_id),
                "document_id": ObjectId(document_id)
            }
            
            if session_id:
                filter_query["session_id"] = session_id
            
            cursor = self.chat_collection.find(filter_query).sort("created_at", -1).limit(limit)
            
            messages = []
            async for message in cursor:
                message_dict = {
                    "id": str(message["_id"]),
                    "question": message["question"],
                    "answer": message["answer"],
                    "sources": message.get("sources", []),
                    "confidence": message.get("confidence", 0.0),
                    "created_at": message["created_at"]
                }
                messages.append(message_dict)
            
            # Return in chronological order (oldest first)
            return list(reversed(messages))

        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []

    async def delete_chat_history(
        self,
        user_id: str,
        document_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Delete chat history"""
        try:
            filter_query = {
                "user_id": ObjectId(user_id),
                "document_id": ObjectId(document_id)
            }
            
            if session_id:
                filter_query["session_id"] = session_id
            
            result = await self.chat_collection.delete_many(filter_query)
            
            return {
                "message": f"Deleted {result.deleted_count} chat messages"
            }

        except Exception as e:
            logger.error(f"Error deleting chat history: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting chat history"
            )

    async def get_document_chat_stats(self, user_id: str, document_id: str) -> Dict[str, Any]:
        """Get chat statistics for a document"""
        try:
            pipeline = [
                {
                    "$match": {
                        "user_id": ObjectId(user_id),
                        "document_id": ObjectId(document_id)
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_messages": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence"},
                        "unique_sessions": {"$addToSet": "$session_id"}
                    }
                }
            ]
            
            result = await self.chat_collection.aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                return {
                    "total_messages": stats["total_messages"],
                    "average_confidence": round(stats["avg_confidence"], 2),
                    "unique_sessions": len([s for s in stats["unique_sessions"] if s is not None])
                }
            else:
                return {
                    "total_messages": 0,
                    "average_confidence": 0.0,
                    "unique_sessions": 0
                }

        except Exception as e:
            logger.error(f"Error getting chat stats: {e}")
            return {
                "total_messages": 0,
                "average_confidence": 0.0,
                "unique_sessions": 0
            }

# Global RAG service instance
rag_service = RAGService()