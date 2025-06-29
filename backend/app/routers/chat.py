from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
import json
from datetime import datetime

from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str
    timestamp: str

class SessionRequest(BaseModel):
    document_id: str

async def get_current_user_id() -> str:
    return "temp_user_123"

@router.post("/process-document/{doc_id}", response_model=ChatResponse)
async def process_document_for_chat(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Process document content for RAG system"""
    try:
        success = await chat_service.process_document_for_chat(doc_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="ไม่สามารถประมวลผลเอกสารได้")
        
        return ChatResponse(
            success=True,
            data={"document_id": doc_id, "processed": True},
            message="ประมวลผลเอกสารสำหรับระบบ chat สำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error processing document for chat: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/session", response_model=ChatResponse)
async def create_chat_session(
    request: SessionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new chat session"""
    try:
        session_id = await chat_service.create_chat_session(user_id, request.document_id)
        
        return ChatResponse(
            success=True,
            data={
                "session_id": session_id,
                "document_id": request.document_id,
                "user_id": user_id
            },
            message="สร้างเซสชันการสนทนาสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ask/{doc_id}", response_model=ChatResponse)
async def ask_question(
    doc_id: str,
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Ask a question about a document using RAG"""
    try:
        result = await chat_service.answer_question(
            document_id=doc_id,
            question=request.question,
            user_id=user_id,
            session_id=request.session_id
        )
        
        # Update session activity if session_id provided
        if request.session_id:
            await chat_service.update_session_activity(request.session_id)
        
        return ChatResponse(
            success=True,
            data={
                "chat_id": result["chat_id"],
                "question": request.question,
                "answer": result["answer"],
                "sources": result["sources"],
                "confidence": result["confidence"],
                "document_title": result["document_title"]
            },
            message="ตอบคำถามสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ask-stream/{doc_id}")
async def ask_question_stream(
    doc_id: str,
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Ask a question with streaming response"""
    try:
        async def generate_response():
            try:
                # First, find relevant chunks
                relevant_chunks = await chat_service.find_relevant_chunks(doc_id, request.question, top_k=5)
                
                if not relevant_chunks:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'ไม่พบข้อมูลที่เกี่ยวข้องในเอกสาร'})}\n\n"
                    return

                # Send chunks found event
                yield f"data: {json.dumps({'type': 'chunks_found', 'count': len(relevant_chunks)})}\n\n"
                
                # Get full answer (non-streaming for now, but can be enhanced)
                result = await chat_service.answer_question(
                    document_id=doc_id,
                    question=request.question,
                    user_id=user_id,
                    session_id=request.session_id
                )
                
                # Send answer in chunks for streaming effect
                answer = result["answer"]
                chunk_size = 50  # characters per chunk
                
                for i in range(0, len(answer), chunk_size):
                    chunk = answer[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
                
                # Send sources
                yield f"data: {json.dumps({'type': 'sources', 'sources': result['sources']})}\n\n"
                
                # Send completion
                yield f"data: {json.dumps({'type': 'complete', 'chat_id': result['chat_id'], 'confidence': result['confidence']})}\n\n"
                
                # Update session activity if session_id provided
                if request.session_id:
                    await chat_service.update_session_activity(request.session_id)
                
            except Exception as e:
                logger.error(f"Error in streaming response: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in streaming endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history/{doc_id}", response_model=ChatResponse)
async def get_document_chat_history(
    doc_id: str,
    session_id: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id)
):
    """Get chat history for a document"""
    try:
        history = await chat_service.get_chat_history(
            user_id=user_id,
            document_id=doc_id,
            session_id=session_id,
            limit=limit
        )
        
        return ChatResponse(
            success=True,
            data={
                "document_id": doc_id,
                "session_id": session_id,
                "total_messages": len(history),
                "messages": history
            },
            message="ดึงประวัติการสนทนาสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงประวัติการสนทนา")

@router.get("/sessions", response_model=ChatResponse)
async def get_chat_sessions(
    user_id: str = Depends(get_current_user_id)
):
    """Get user's chat sessions"""
    try:
        sessions = await chat_service.get_chat_sessions(user_id)
        
        return ChatResponse(
            success=True,
            data={
                "user_id": user_id,
                "total_sessions": len(sessions),
                "sessions": sessions
            },
            message="ดึงรายการเซสชันการสนทนาสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting chat sessions: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงรายการเซสชัน")

@router.get("/search", response_model=ChatResponse)
async def search_chat_history(
    query: str,
    doc_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Search through chat history"""
    try:
        results = await chat_service.search_chat_history(
            user_id=user_id,
            search_query=query,
            document_id=doc_id
        )
        
        return ChatResponse(
            success=True,
            data={
                "query": query,
                "document_id": doc_id,
                "total_results": len(results),
                "results": results
            },
            message=f"พบผลการค้นหา {len(results)} รายการ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error searching chat history: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการค้นหา")

@router.get("/stats/{doc_id}", response_model=ChatResponse)
async def get_document_chat_stats(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get chat statistics for a document"""
    try:
        stats = await chat_service.get_document_chat_stats(doc_id)
        
        return ChatResponse(
            success=True,
            data={
                "document_id": doc_id,
                "stats": stats
            },
            message="ดึงสถิติการสนทนาสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting document chat stats: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงสถิติ")

@router.get("/chunks/{doc_id}", response_model=ChatResponse)
async def get_document_chunks(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get processed chunks for a document (for debugging)"""
    try:
        from app.database.mongodb import get_collection
        chunk_collection = get_collection("document_chunks")
        
        chunks = []
        async for chunk in chunk_collection.find({"document_id": doc_id}):
            chunks.append({
                "chunk_id": chunk["chunk_id"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "start_pos": chunk["start_pos"],
                "end_pos": chunk["end_pos"]
            })
        
        return ChatResponse(
            success=True,
            data={
                "document_id": doc_id,
                "total_chunks": len(chunks),
                "chunks": chunks
            },
            message=f"ดึงข้อมูล chunks จำนวน {len(chunks)} รายการ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error getting document chunks: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงข้อมูล chunks")

@router.delete("/session/{session_id}", response_model=ChatResponse)
async def delete_chat_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a chat session and its history"""
    try:
        from app.database.mongodb import get_collection
        
        # Delete session
        session_collection = get_collection("chat_sessions")
        session_result = await session_collection.delete_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        if session_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="ไม่พบเซสชันที่ร้องขอ")
        
        # Delete chat history for this session
        chat_result = await chat_service.chat_collection.delete_many({
            "session_id": session_id,
            "user_id": user_id
        })
        
        return ChatResponse(
            success=True,
            data={
                "session_id": session_id,
                "messages_deleted": chat_result.deleted_count
            },
            message="ลบเซสชันการสนทนาสำเร็จ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการลบเซสชัน")

@router.get("/similar/{doc_id}", response_model=ChatResponse)
async def find_similar_content(
    doc_id: str,
    query: str,
    top_k: int = 5,
    user_id: str = Depends(get_current_user_id)
):
    """Find similar content chunks for a query"""
    try:
        chunks = await chat_service.find_relevant_chunks(doc_id, query, top_k)
        
        return ChatResponse(
            success=True,
            data={
                "document_id": doc_id,
                "query": query,
                "total_chunks": len(chunks),
                "chunks": chunks
            },
            message=f"พบเนื้อหาที่คล้ายกัน {len(chunks)} รายการ",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error finding similar content: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการค้นหาเนื้อหา")