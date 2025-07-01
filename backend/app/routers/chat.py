from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
import json
from datetime import datetime

from app.services.rag_service import RAGService, get_rag_service
from app.core.exceptions import RAGError

logger = logging.getLogger(__name__)

router = APIRouter()

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

async def get_current_user_id() -> str:
    return "temp_user_123"

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Ask a question using RAG across documents"""
    try:
        # Use RAG service to search and generate answer
        rag_response = await rag_service.search_and_generate(
            query=request.question,
            user_id=user_id,
            document_ids=request.document_ids,
            top_k=request.top_k,
            streaming=request.streaming
        )

        
        return ChatResponse(
            success=True,
            data={
                "question": request.question,
                "answer": rag_response.answer,
                "confidence_score": rag_response.confidence_score,
                "response_time": rag_response.response_time,
                "sources": rag_response.context.sources,
                "sources_count": rag_response.sources_count,
                "total_chunks_found": rag_response.context.total_chunks,
                "avg_similarity": rag_response.context.avg_similarity
            },
            message="ตอบคำถามสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except RAGError as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการตอบคำถาม")

@router.post("/search", response_model=ChatResponse)
async def search_documents(
    request: SearchRequest,
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Search documents without generating answers"""
    try:
        results = await rag_service.search_documents_only(
            query=request.query,
            user_id=user_id,
            document_ids=request.document_ids,
            top_k=request.top_k
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
    rag_service: RAGService = Depends(get_rag_service)
):
    """Ask a question with streaming response"""
    try:
        async def generate_streaming_response():
            try:
                # Generate streaming response from RAG service
                rag_response = await rag_service.search_and_generate(
                    query=request.question,
                    user_id=user_id,
                    document_ids=request.document_ids,
                    top_k=request.top_k,
                    streaming=True
                )
                
                # Send metadata first
                metadata = {
                    "type": "metadata",
                    "confidence_score": rag_response.confidence_score,
                    "sources_count": rag_response.sources_count,
                    "response_time": rag_response.response_time
                }
                yield f"data: {json.dumps(metadata)}\n\n"
                
                # Send sources
                sources_data = {
                    "type": "sources",
                    "sources": rag_response.context.sources
                }
                yield f"data: {json.dumps(sources_data)}\n\n"
                
                # Stream answer in chunks
                answer = rag_response.answer
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
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get similar questions for suggestion"""
    try:
        similar_questions = await rag_service.get_similar_questions(
            query=query,
            user_id=user_id,
            limit=limit
        )
        
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
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get RAG system statistics"""
    try:
        stats = rag_service.get_search_statistics()
        
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
    rag_service: RAGService = Depends(get_rag_service)
):
    """Health check for RAG system"""
    try:
        # Simple health check
        stats = rag_service.get_search_statistics()
        
        health_status = {
            "rag_service": "healthy",
            "embedding_service": "healthy",
            "documents_indexed": stats.get("total_documents_indexed", 0),
            "chunks_available": stats.get("total_chunks_available", 0)
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