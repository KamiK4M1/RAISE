import asyncio
import uuid
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
from dataclasses import dataclass
from enum import Enum
from fastapi import Depends

from app.database.mongodb import get_collection
from app.core.embeddings import embedding_service
from app.core.ai_models import together_ai
from app.services.document_processor import document_processor
from app.core.exceptions import RAGError
from app.utils.thai_processing import thai_processor

logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class RetrievedChunk:
    """Represents a retrieved document chunk with metadata"""
    text: str
    similarity_score: float
    document_id: str
    document_title: str
    chunk_index: int
    confidence_level: ConfidenceLevel

@dataclass
class RAGContext:
    """Context assembled from retrieved chunks"""
    chunks: List[RetrievedChunk]
    total_chunks: int
    avg_similarity: float
    context_text: str
    sources: List[Dict[str, Any]]

@dataclass
class RAGResponse:
    """Complete RAG response with answer and metadata"""
    answer: str
    context: RAGContext
    query: str
    response_time: float
    confidence_score: float
    sources_count: int
    streaming: bool = False

class RAGService:
    def __init__(self):
        self.similarity_threshold = 0.7
        self.max_context_length = 4000
        self.top_k_retrieval = 10
        self.final_k_selection = 5

        self.documents_collection = get_collection("documents")
        self.chunks_collection = get_collection("chunks")

        self.embedding_service = embedding_service
        self.llm = together_ai

        # Prompt templates
        self.system_prompt_template = """คุณเป็นผู้ช่วยตอบคำถามที่เชี่ยวชาญในระบบ RAG (Retrieval-Augmented Generation)

หน้าที่ของคุณ:
1. ตอบคำถามโดยอิงจากเนื้อหาที่ให้มาเท่านั้น
2. ให้คำตอบที่แม่นยำและครบถ้วน
3. อ้างอิงแหล่งที่มาอย่างชัดเจน
4. หากไม่มีข้อมูลเพียงพอ ให้บอกว่าไม่สามารถตอบได้

หลักการตอบ:
- ใช้ภาษาไทยหรือภาษาอังกฤษตามที่เหมาะสม
- ตอบให้กระชับแต่ครอบคลุม
- ระบุความมั่นใจในการตอบ
- แยกแยะข้อเท็จจริงและความคิดเห็น"""

        self.answer_prompt_template = """ตามบริบทที่ให้มา กรุณาตอบคำถามต่อไปนี้:

บริบท:
{context}

คำถาม: {query}

คำตอบ:"""

    async def search_and_generate(
        self,
        query: str,
        user_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        streaming: bool = False
    ) -> RAGResponse:
        """Main RAG pipeline: search documents and generate answer"""
        start_time = asyncio.get_event_loop().time()

        try:
            retrieved_chunks = await self.semantic_search(
                query=query,
                user_id=user_id,
                document_ids=document_ids,
                top_k=top_k or self.top_k_retrieval,
            )

            if not retrieved_chunks:
                return RAGResponse(
                    answer="ขออภัย ไม่พบข้อมูลที่เกี่ยวข้องกับคำถามของคุณในเอกสารที่มีอยู่",
                    context=RAGContext(
                        chunks=[],
                        total_chunks=0,
                        avg_similarity=0.0,
                        context_text="",
                        sources=[]
                    ),
                    query=query,
                    response_time=0.0,
                    confidence_score=0.0,
                    sources_count=0,
                    streaming=streaming
                )

            # Step 2: Rank and select best chunks
            selected_chunks = await self.rank_and_select_chunks(
                chunks=retrieved_chunks,
                query=query,
                max_chunks=self.final_k_selection
            )

            context = await self.assemble_context(selected_chunks)
            answer = await self.generate_answer(query, context)

            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            confidence_score = self.calculate_confidence_score(context, answer)

            return RAGResponse(
                answer=answer,
                context=context,
                query=query,
                response_time=response_time,
                confidence_score=confidence_score,
                sources_count=len(context.sources),
                streaming=streaming
            )

        except Exception as e:
            logger.error(f"RAG pipeline error: {e}")
            raise RAGError(f"เกิดข้อผิดพลาดในระบบ RAG: {str(e)}")

    async def semantic_search(
        self,
        query: str,
        user_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 10,
    ) -> List[RetrievedChunk]:
        """Perform semantic search across document chunks"""
        try:
            query_embedding = await self.embedding_service.generate_single_embedding(query)
            if not query_embedding:
                raise RAGError("ไม่สามารถสร้าง embedding สำหรับคำค้นหาได้")

            documents_collection = get_collection("documents")
            document_filter = {"userId": user_id, "status": "completed"}
            if document_ids:
                document_filter["_id"] = {"$in": document_ids}

            documents = await documents_collection.find(document_filter).to_list(length=100)
            if not documents:
                return []

            all_chunks = []
            chunks_collection = get_collection("chunks")
            doc_ids = [str(doc['_id']) for doc in documents]

            async for chunk in chunks_collection.find({"document_id": {"$in": doc_ids}}):
                 if 'embedding' in chunk:
                    doc = next((d for d in documents if str(d['_id']) == chunk['document_id']), None)
                    if doc:
                        all_chunks.append({**chunk, 'document_title': doc['title']})

            if not all_chunks:
                logger.warning("No chunks with embeddings found for the given documents.")
                return []

            logger.info(f"Searching across {len(documents)} documents with {len(all_chunks)} total chunks.")

            # Calculate similarities
            similarities = []
            query_emb_np = np.array(query_embedding)

            for i, chunk in enumerate(all_chunks):
                chunk_emb_np = np.array(chunk['embedding'])
                similarity = np.dot(query_emb_np, chunk_emb_np) / (
                    np.linalg.norm(query_emb_np) * np.linalg.norm(chunk_emb_np)
                )
                similarities.append({
                    'index': i,
                    'similarity': float(similarity),
                    'chunk': chunk
                })

            # Filter by similarity threshold and sort
            relevant_chunks = [
                sim for sim in similarities
                if sim['similarity'] >= self.similarity_threshold
            ]
            relevant_chunks.sort(key=lambda x: x['similarity'], reverse=True)
            top_chunks = relevant_chunks[:top_k]
            logger.info(f"Found {len(top_chunks)} relevant chunks above threshold {self.similarity_threshold}")

            # Convert to RetrievedChunk objects
            retrieved_chunks = []
            for sim in top_chunks:
                chunk = sim['chunk']
                confidence_level = self._determine_confidence_level(sim['similarity'])
                retrieved_chunks.append(RetrievedChunk(
                    text=chunk['text'],
                    similarity_score=sim['similarity'],
                    document_id=chunk['document_id'],
                    document_title=chunk['document_title'],
                    chunk_index=chunk['chunkIndex'],
                    confidence_level=confidence_level
                ))
            return retrieved_chunks

        except Exception as e:
            logger.error(f"Semantic search error: {e}", exc_info=True)
            raise RAGError(f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}")


    async def rank_and_select_chunks(
        self,
        chunks: List[RetrievedChunk],
        query: str,
        max_chunks: int = 5
    ) -> List[RetrievedChunk]:
        """Advanced ranking and selection of retrieved chunks"""
        if len(chunks) <= max_chunks:
            return chunks

        try:
            # Score chunks based on multiple factors
            scored_chunks = []
            for chunk in chunks:
                score = chunk.similarity_score
                if chunk.confidence_level == ConfidenceLevel.HIGH:
                    score *= 1.2
                elif chunk.confidence_level == ConfidenceLevel.MEDIUM:
                    score *= 1.1

                text_length_factor = min(len(chunk.text) / 1000, 1.5)
                score *= (0.8 + 0.4 * text_length_factor)

                query_terms = set(thai_processor.tokenize(query.lower()))
                chunk_terms = set(thai_processor.tokenize(chunk.text.lower()))

                if query_terms and chunk_terms:
                    term_overlap = len(query_terms.intersection(chunk_terms)) / len(query_terms)
                    score *= (1.0 + 0.3 * term_overlap)
                scored_chunks.append((score, chunk))

            scored_chunks.sort(key=lambda x: x[0], reverse=True)

            # Select top chunks ensuring diversity
            selected_chunks = []
            selected_docs = set()
            for score, chunk in scored_chunks:
                if len(selected_chunks) >= max_chunks:
                    break
                if len(selected_chunks) < max_chunks // 2 or chunk.document_id not in selected_docs:
                    selected_chunks.append(chunk)
                    selected_docs.add(chunk.document_id)

            if len(selected_chunks) < max_chunks:
                for score, chunk in scored_chunks:
                    if len(selected_chunks) >= max_chunks:
                        break
                    if chunk not in selected_chunks:
                        selected_chunks.append(chunk)

            logger.info(f"Selected {len(selected_chunks)} chunks from {len(chunks)} candidates")
            return selected_chunks

        except Exception as e:
            logger.error(f"Chunk ranking error: {e}")
            return sorted(chunks, key=lambda x: x.similarity_score, reverse=True)[:max_chunks]

    async def assemble_context(self, chunks: List[RetrievedChunk]) -> RAGContext:
        """Assemble context from selected chunks"""
        if not chunks:
            return RAGContext(chunks=[], total_chunks=0, avg_similarity=0.0, context_text="", sources=[])

        try:
            context_parts = []
            sources = []
            seen_sources = set()

            for i, chunk in enumerate(chunks):
                context_parts.append(f"[แหล่งที่ {i+1}] {chunk.text}")
                source_key = f"{chunk.document_id}_{chunk.document_title}"
                if source_key not in seen_sources:
                    sources.append({
                        "document_id": chunk.document_id,
                        "document_title": chunk.document_title,
                        "similarity_score": chunk.similarity_score,
                        "confidence_level": chunk.confidence_level.value,
                        "chunk_count": 1
                    })
                    seen_sources.add(source_key)
                else:
                    for source in sources:
                        if source["document_id"] == chunk.document_id:
                            source["chunk_count"] += 1
                            source["similarity_score"] = max(source["similarity_score"], chunk.similarity_score)
                            break

            context_text = "\n\n".join(context_parts)
            if len(context_text) > self.max_context_length:
                context_text = context_text[:self.max_context_length] + "..."
                logger.warning(f"Context trimmed to {self.max_context_length} characters")

            avg_similarity = sum(chunk.similarity_score for chunk in chunks) / len(chunks)

            return RAGContext(
                chunks=chunks,
                total_chunks=len(chunks),
                avg_similarity=avg_similarity,
                context_text=context_text,
                sources=sources
            )
        except Exception as e:
            logger.error(f"Context assembly error: {e}")
            raise RAGError(f"เกิดข้อผิดพลาดในการประกอบบริบท: {str(e)}")

    async def generate_answer(self, query: str, context: RAGContext) -> str:
        """Generate answer using Together AI"""
        try:
            prompt = self.answer_prompt_template.format(context=context.context_text, query=query)
            answer = await together_ai.generate_response(
                prompt=prompt,
                system_prompt=self.system_prompt_template,
                max_tokens=1000,
                temperature=0.3
            )
            answer = self._post_process_answer(answer, context)
            logger.info(f"Generated answer of length {len(answer)}")
            return answer
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            raise RAGError(f"เกิดข้อผิดพลาดในการสร้างคำตอบ: {str(e)}")

    async def generate_streaming_answer(self, query: str, context: RAGContext) -> AsyncGenerator[str, None]:
        """Generate streaming answer"""
        answer = await self.generate_answer(query, context)
        chunk_size = 50
        for i in range(0, len(answer), chunk_size):
            chunk = answer[i:i + chunk_size]
            yield chunk
            await asyncio.sleep(0.1)

    def calculate_confidence_score(self, context: RAGContext, answer: str) -> float:
        """Calculate confidence score for the generated answer"""
        try:
            if not context.chunks:
                return 0.0

            base_score = context.avg_similarity
            high_conf_chunks = sum(1 for chunk in context.chunks if chunk.confidence_level == ConfidenceLevel.HIGH)
            source_boost = min(high_conf_chunks * 0.1, 0.3)
            length_boost = min(len(answer) / 500, 0.2) if answer else 0
            context_penalty = 0.2 if len(context.context_text) < 200 else 0.0

            confidence = min(base_score + source_boost + length_boost - context_penalty, 1.0)
            return max(confidence, 0.0)
        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return 0.5

    def _determine_confidence_level(self, similarity_score: float) -> ConfidenceLevel:
        """Determine confidence level based on similarity score"""
        if similarity_score >= 0.85:
            return ConfidenceLevel.HIGH
        elif similarity_score >= 0.75:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _post_process_answer(self, answer: str, context: RAGContext) -> str:
        """Post-process generated answer"""
        try:
            answer = answer.strip()
            if context.sources and "แหล่งที่มา" not in answer and "อ้างอิง" not in answer:
                source_info = "\n\nแหล่งที่มา:\n"
                for i, source in enumerate(context.sources[:3]):
                    source_info += f"- {source['document_title']} (ความเชื่อมั่น: {source['confidence_level']})\n"
                answer += source_info
            return answer
        except Exception as e:
            logger.error(f"Answer post-processing error: {e}")
            return answer

    async def search_documents_only(
        self,
        query: str,
        user_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search documents without generating answers"""
        try:
            chunks = await self.semantic_search(
                query=query,
                user_id=user_id,
                document_ids=document_ids,
                top_k=top_k
            )
            results = []
            for chunk in chunks:
                results.append({
                    "document_id": chunk.document_id,
                    "document_title": chunk.document_title,
                    "text_preview": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                    "similarity_score": chunk.similarity_score,
                    "confidence_level": chunk.confidence_level.value,
                    "chunk_index": chunk.chunk_index
                })
            return results
        except Exception as e:
            logger.error(f"Document search error: {e}")
            raise RAGError(f"เกิดข้อผิดพลาดในการค้นหาเอกสาร: {str(e)}")

    async def get_similar_questions(self, query: str, user_id: str, limit: int = 5) -> List[str]:
        """Get similar questions based on query"""
        try:
            # Placeholder implementation
            base_variations = [
                f"อธิบายเกี่ยวกับ {query}",
                f"{query} คืออะไร",
                f"ยกตัวอย่าง {query}",
                f"วิธีการ {query}",
                f"ขั้นตอนของ {query}"
            ]
            return base_variations[:limit]
        except Exception as e:
            logger.error(f"Similar questions error: {e}")
            return []

    def get_search_statistics(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        try:
            # In a real scenario, you'd query the database for these stats
            # This implementation relies on a potentially incomplete cache
            total_documents = len(document_processor._document_chunks_cache)
            total_chunks = sum(len(chunks) for chunks in document_processor._document_chunks_cache.values())
            return {
                "total_documents_indexed": total_documents,
                "total_chunks_available": total_chunks,
                "similarity_threshold": self.similarity_threshold,
                "max_context_length": self.max_context_length,
                "top_k_retrieval": self.top_k_retrieval,
                "final_k_selection": self.final_k_selection,
                "embedding_dimension": embedding_service.get_embedding_dimension()
            }
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {}

# Global instance
# rag_service = RAGService()

def get_rag_service() -> RAGService:
    """Dependency injector for the RAGService."""
    return RAGService()