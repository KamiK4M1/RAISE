import asyncio
import uuid
from typing import List, Dict, Optional, Any, AsyncGenerator
from datetime import datetime
import logging

from app.core.ai_models import together_ai
from app.core.embeddings import embedding_service
from app.database.mongodb import get_collection
from app.core.exceptions import ModelError

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self._chat_collection = None
        self._document_collection = None
        self._chunk_collection = None
    
    @property
    def chat_collection(self):
        if self._chat_collection is None:
            self._chat_collection = get_collection("chat_history")
        return self._chat_collection
    
    @property
    def document_collection(self):
        if self._document_collection is None:
            self._document_collection = get_collection("documents")
        return self._document_collection
    
    @property
    def chunk_collection(self):
        if self._chunk_collection is None:
            self._chunk_collection = get_collection("document_chunks")
        return self._chunk_collection

    async def process_document_for_chat(self, document_id: str) -> bool:
        """Process document content for RAG system by creating searchable chunks"""
        try:
            # Get document
            document = await self.document_collection.find_one({"document_id": document_id})
            if not document:
                raise ValueError(f"Document {document_id} not found")

            content = document.get("content", "")
            if not content:
                raise ValueError("Document has no content")

            # Split content into chunks
            chunks = self._split_content_into_chunks(content)
            
            # Generate embeddings for chunks
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings(chunk_texts)

            # Prepare chunks for database
            chunk_documents = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_doc = {
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk["text"],
                    "start_pos": chunk["start_pos"],
                    "end_pos": chunk["end_pos"],
                    "embedding": embedding,
                    "created_at": datetime.utcnow()
                }
                chunk_documents.append(chunk_doc)

            # Store chunks in database
            if chunk_documents:
                await self.chunk_collection.insert_many(chunk_documents)
                
                # Update document to mark as processed
                await self.document_collection.update_one(
                    {"document_id": document_id},
                    {"$set": {"chat_processed": True, "total_chunks": len(chunk_documents)}}
                )

            logger.info(f"Processed document {document_id} into {len(chunk_documents)} chunks")
            return True

        except Exception as e:
            logger.error(f"Error processing document for chat: {e}")
            return False

    def _split_content_into_chunks(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Split content into overlapping chunks for RAG"""
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence ending within next 100 characters
                for i in range(end, min(end + 100, len(content))):
                    if content[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_text = content[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "start_pos": start,
                    "end_pos": end
                })
            
            start = max(start + chunk_size - overlap, end)
            
            if start >= len(content):
                break
        
        return chunks

    async def find_relevant_chunks(
        self, 
        document_id: str, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find relevant chunks for a query using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = await embedding_service.generate_single_embedding(query)
            
            # Get all chunks for the document
            chunks = []
            async for chunk in self.chunk_collection.find({"document_id": document_id}):
                chunks.append(chunk)
            
            if not chunks:
                return []

            # Calculate similarities
            similarities = []
            for chunk in chunks:
                similarity = await embedding_service.compute_similarity(
                    query_embedding, 
                    chunk["embedding"]
                )
                similarities.append({
                    "chunk": chunk,
                    "similarity": similarity
                })

            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return [
                {
                    "chunk_id": item["chunk"]["chunk_id"],
                    "text": item["chunk"]["text"],
                    "similarity": item["similarity"],
                    "start_pos": item["chunk"]["start_pos"],
                    "end_pos": item["chunk"]["end_pos"]
                }
                for item in similarities[:top_k]
            ]

        except Exception as e:
            logger.error(f"Error finding relevant chunks: {e}")
            return []

    async def answer_question(
        self, 
        document_id: str, 
        question: str, 
        user_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Answer a question using RAG (Retrieval-Augmented Generation)"""
        try:
            # Find relevant chunks
            relevant_chunks = await self.find_relevant_chunks(document_id, question, top_k=5)
            
            if not relevant_chunks:
                return {
                    "answer": "ขออภัย ไม่พบข้อมูลที่เกี่ยวข้องในเอกสารนี้",
                    "sources": [],
                    "confidence": 0.0
                }

            # Prepare context from chunks
            context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])
            
            # Get document info for better context
            document = await self.document_collection.find_one({"document_id": document_id})
            doc_title = document.get("title", "Unknown Document") if document else "Unknown Document"

            # Generate answer using AI
            answer = await together_ai.answer_question(question, context)
            
            # Calculate confidence based on similarity scores
            avg_similarity = sum([chunk["similarity"] for chunk in relevant_chunks]) / len(relevant_chunks)
            confidence = min(avg_similarity * 100, 100)

            # Prepare sources
            sources = [
                {
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                    "similarity": chunk["similarity"],
                    "position": f"{chunk['start_pos']}-{chunk['end_pos']}"
                }
                for chunk in relevant_chunks
            ]

            # Save chat history
            chat_id = str(uuid.uuid4())
            chat_record = {
                "chat_id": chat_id,
                "session_id": session_id,
                "document_id": document_id,
                "user_id": user_id,
                "question": question,
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "created_at": datetime.utcnow()
            }
            
            await self.chat_collection.insert_one(chat_record)

            return {
                "chat_id": chat_id,
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "document_title": doc_title
            }

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            raise ModelError(f"Failed to answer question: {str(e)}")

    async def get_chat_history(
        self, 
        user_id: str, 
        document_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get chat history for user"""
        try:
            query = {"user_id": user_id}
            if document_id:
                query["document_id"] = document_id
            if session_id:
                query["session_id"] = session_id

            history = []
            async for chat in self.chat_collection.find(query).sort("created_at", -1).limit(limit):
                history.append({
                    "chat_id": chat["chat_id"],
                    "session_id": chat.get("session_id"),
                    "document_id": chat["document_id"],
                    "question": chat["question"],
                    "answer": chat["answer"],
                    "confidence": chat.get("confidence", 0),
                    "created_at": chat["created_at"]
                })

            return history

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    async def create_chat_session(self, user_id: str, document_id: str) -> str:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        
        # Save session info
        session_record = {
            "session_id": session_id,
            "user_id": user_id,
            "document_id": document_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        session_collection = get_collection("chat_sessions")
        await session_collection.insert_one(session_record)
        
        return session_id

    async def update_session_activity(self, session_id: str):
        """Update session last activity"""
        try:
            session_collection = get_collection("chat_sessions")
            await session_collection.update_one(
                {"session_id": session_id},
                {"$set": {"last_activity": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")

    async def get_chat_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's chat sessions"""
        try:
            session_collection = get_collection("chat_sessions")
            sessions = []
            
            async for session in session_collection.find({"user_id": user_id}).sort("last_activity", -1):
                # Get document info
                document = await self.document_collection.find_one({"document_id": session["document_id"]})
                doc_title = document.get("title", "Unknown Document") if document else "Unknown Document"
                
                # Count messages in session
                message_count = await self.chat_collection.count_documents({"session_id": session["session_id"]})
                
                sessions.append({
                    "session_id": session["session_id"],
                    "document_id": session["document_id"],
                    "document_title": doc_title,
                    "message_count": message_count,
                    "created_at": session["created_at"],
                    "last_activity": session["last_activity"]
                })
            
            return sessions

        except Exception as e:
            logger.error(f"Error getting chat sessions: {e}")
            return []

    async def search_chat_history(
        self,
        user_id: str,
        search_query: str,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search through chat history"""
        try:
            query = {
                "user_id": user_id,
                "$or": [
                    {"question": {"$regex": search_query, "$options": "i"}},
                    {"answer": {"$regex": search_query, "$options": "i"}}
                ]
            }
            
            if document_id:
                query["document_id"] = document_id

            results = []
            async for chat in self.chat_collection.find(query).sort("created_at", -1):
                # Get document info
                document = await self.document_collection.find_one({"document_id": chat["document_id"]})
                doc_title = document.get("title", "Unknown Document") if document else "Unknown Document"
                
                results.append({
                    "chat_id": chat["chat_id"],
                    "document_id": chat["document_id"],
                    "document_title": doc_title,
                    "question": chat["question"],
                    "answer": chat["answer"],
                    "confidence": chat.get("confidence", 0),
                    "created_at": chat["created_at"]
                })

            return results

        except Exception as e:
            logger.error(f"Error searching chat history: {e}")
            return []

    async def get_document_chat_stats(self, document_id: str) -> Dict[str, Any]:
        """Get chat statistics for a document"""
        try:
            # Count total questions
            total_questions = await self.chat_collection.count_documents({"document_id": document_id})
            
            # Get average confidence
            pipeline = [
                {"$match": {"document_id": document_id}},
                {"$group": {"_id": None, "avg_confidence": {"$avg": "$confidence"}}}
            ]
            
            avg_confidence = 0
            async for result in self.chat_collection.aggregate(pipeline):
                avg_confidence = result.get("avg_confidence", 0)

            # Count unique users
            unique_users = len(await self.chat_collection.distinct("user_id", {"document_id": document_id}))
            
            # Get most frequent question types (simple keyword analysis)
            frequent_keywords = await self._get_frequent_keywords(document_id)

            return {
                "total_questions": total_questions,
                "average_confidence": round(avg_confidence, 2),
                "unique_users": unique_users,
                "frequent_keywords": frequent_keywords
            }

        except Exception as e:
            logger.error(f"Error getting document chat stats: {e}")
            return {"error": str(e)}

    async def _get_frequent_keywords(self, document_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get frequently asked keywords from questions"""
        try:
            # Simple keyword extraction (in production, use more sophisticated NLP)
            keyword_counts = {}
            
            async for chat in self.chat_collection.find({"document_id": document_id}):
                question = chat.get("question", "").lower()
                # Remove common Thai stop words and extract meaningful terms
                words = question.split()
                for word in words:
                    if len(word) > 2 and word not in ["คือ", "ไม่", "และ", "หรือ", "ของ", "ที่", "เป็น"]:
                        keyword_counts[word] = keyword_counts.get(word, 0) + 1

            # Sort by frequency
            sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {"keyword": keyword, "count": count}
                for keyword, count in sorted_keywords[:limit]
            ]

        except Exception as e:
            logger.error(f"Error getting frequent keywords: {e}")
            return []

# Global instance
chat_service = ChatService()