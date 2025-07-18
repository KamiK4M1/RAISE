from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
import json
from datetime import datetime

from app.services.rag_service import MongoDBRAG, get_rag_service
from app.services.chat_service import ChatService
from app.core.exceptions import RAGError
from app.core.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()

# Global chat service instance
chat_service = ChatService()

def get_chat_service() -> ChatService:
    return chat_service

class ChatRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None
    streaming: Optional[bool] = False
    top_k: Optional[int] = 5

class SearchRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = 5

class ChatResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str
    timestamp: str

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Ask a question using RAG with LLM integration across all user documents"""
    try:
        # Generate answer using ChatService across all user documents
        result = await chat_service.answer_question_across_documents(
            question=request.question,
            user_id=user_id,
            document_ids=request.document_ids  # Optional: can limit to specific documents
        )
        
        # Extract answer from result
        answer = result["answer"]
        
        return ChatResponse(
            success=True,
            data={
                "question": request.question,
                "answer": answer,
                "confidence_score": result["confidence"],
                "response_time": 0.0,
                "sources": result["sources"],
                "sources_count": len(result["sources"]),
                "total_chunks_found": len(result["sources"]),
                "avg_similarity": result["confidence"],
                "documents_searched": result.get("documents_searched", 0),
                "documents_with_results": result.get("documents_with_results", [])
            },
            message="ตอบคำถามสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการตอบคำถาม")

@router.post("/process-document/{document_id}")
async def process_document_for_chat(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Process a document for chat functionality"""
    try:
        success = await chat_service.process_document_for_chat(document_id)
        return {
            "success": success,
            "message": "เอกสารถูกประมวลผลสำเร็จ" if success else "เกิดข้อผิดพลาดในการประมวลผลเอกสาร",
            "document_id": document_id
        }
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการประมวลผลเอกสาร: {str(e)}")

@router.post("/search", response_model=ChatResponse)
async def search_documents(
    request: SearchRequest,
    user_id: str = Depends(get_current_user_id),
    rag_service: MongoDBRAG = Depends(get_rag_service)
):
    """Search documents without generating answers"""
    try:
        results = await rag_service.vector_search(
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_ids[0] if request.document_ids else None
        )
        
        return ChatResponse(
            success=True,
            data={
                "query": request.query,
                "total_results": len(results),
                "results": results
            },
            message=f"พบผลการค้นหา {len(results)} รายการ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except RAGError as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการค้นหา")

@router.post("/ask-stream")
async def ask_question_stream(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    rag_service: MongoDBRAG = Depends(get_rag_service)
):
    """Ask a question with streaming response"""
    try:
        async def generate_streaming_response():
            try:
                # Generate response from MongoDB RAG service
                results = await rag_service.vector_search(
                    query=request.question,
                    top_k=request.top_k,
                    document_id=request.document_ids[0] if request.document_ids else None
                )
                
                context = await rag_service.retrieve_context(
                    query=request.question,
                    top_k=request.top_k,
                    document_id=request.document_ids[0] if request.document_ids else None
                )
                
                # Send metadata first
                metadata = {
                    "type": "metadata",
                    "confidence_score": results[0].get('score', 0) if results else 0,
                    "sources_count": len(results),
                    "response_time": 0.0
                }
                yield f"data: {json.dumps(metadata)}\n\n"
                
                # Send sources
                sources_data = {
                    "type": "sources",
                    "sources": [{"text": r.get('text', ''), "score": r.get('score', 0)} for r in results]
                }
                yield f"data: {json.dumps(sources_data)}\n\n"
                
                # Stream answer in chunks
                answer = context if context else "ไม่พบข้อมูลที่เกี่ยวข้องกับคำถามของคุณ"
                chunk_size = 50
                
                for i in range(0, len(answer), chunk_size):
                    chunk = answer[i:i + chunk_size]
                    chunk_data = {
                        "type": "text",
                        "content": chunk
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send completion
                completion_data = {
                    "type": "complete",
                    "total_characters": len(answer)
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                
            except RAGError as e:
                error_data = {
                    "type": "error",
                    "message": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_data = {
                    "type": "error",
                    "message": "เกิดข้อผิดพลาดในการตอบคำถาม"
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_streaming_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in streaming endpoint: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการเริ่มการสตรีม")

@router.get("/similar-questions", response_model=ChatResponse)
async def get_similar_questions(
    query: str,
    limit: int = 5,
    user_id: str = Depends(get_current_user_id),
    rag_service: MongoDBRAG = Depends(get_rag_service)
):
    """Get similar questions for suggestion"""
    try:
        # Simple implementation for similar questions
        similar_questions = [
            f"อธิบายเกี่ยวกับ {query}",
            f"{query} คืออะไร",
            f"ยกตัวอย่าง {query}",
            f"วิธีการ {query}",
            f"ขั้นตอนของ {query}"
        ][:limit]
        
        return ChatResponse(
            success=True,
            data={
                "query": query,
                "similar_questions": similar_questions
            },
            message=f"พบคำถามที่คล้ายกัน {len(similar_questions)} รายการ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting similar questions: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงคำถามที่คล้ายกัน")

@router.get("/stats", response_model=ChatResponse)
async def get_rag_statistics(
    rag_service: MongoDBRAG = Depends(get_rag_service)
):
    """Get RAG system statistics"""
    try:
        stats = await rag_service.get_collection_stats()
        
        return ChatResponse(
            success=True,
            data={"stats": stats},
            message="ดึงสถิติระบบ RAG สำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงสถิติ")

@router.get("/health", response_model=ChatResponse)
async def health_check(
    rag_service: MongoDBRAG = Depends(get_rag_service)
):
    """Health check for RAG system"""
    try:
        # Simple health check
        stats = await rag_service.get_collection_stats()
        
        health_status = {
            "rag_service": "healthy",
            "embedding_service": "healthy",
            "documents_indexed": stats.get("document_count", 0),
            "chunks_available": stats.get("document_count", 0)
        }
        
        return ChatResponse(
            success=True,
            data={"health": health_status},
            message="ระบบ RAG ทำงานปกติ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail="ระบบ RAG มีปัญหา")