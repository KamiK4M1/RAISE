from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from typing import List, Optional
import logging
from datetime import datetime, timezone

from app.models.document import (
    DocumentAPIResponse, 
    DocumentListResponse, 
    DocumentProcessRequest
)
from app.services.document_processor import document_processor
from app.utils.file_handler import file_handler
from app.core.exceptions import FileUploadError, DocumentProcessingError
from app.core.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()

# Authentication is now handled by the dependency

@router.post("/upload", response_model=DocumentAPIResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """Upload and process a document"""
    try:
        # Validate file
        file_handler.validate_file(file.filename, file.size)
        
        # Read file content
        file_content = await file.read()
        
        # Save file
        file_path = await file_handler.save_file(file_content, file.filename)
        
        # Extract file type
        file_type = file.filename.split('.')[-1].lower()
        
        # Start document processing
        document_id = await document_processor.process_document(
            file_path=file_path,
            filename=file.filename,
            file_type=file_type,
            file_size=file.size,
            user_id=user_id,
            title=file.filename  # Use filename as title by default
        )
        
        return DocumentAPIResponse(
            success=True,
            data={
                "document_id": document_id,
                "filename": file.filename,
                "status": "processing"
            },
            message="ไฟล์ถูกอัปโหลดและกำลังประมวลผล",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except FileUploadError as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in upload: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการอัปโหลดไฟล์")

@router.get("/list", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """List user's documents"""
    try:
        documents = await document_processor.list_user_documents(user_id, skip, limit)
        
        return DocumentListResponse(
            success=True,
            data=documents,
            message="ดึงรายการเอกสารสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงรายการเอกสาร")

@router.get("/{doc_id}", response_model=DocumentAPIResponse)
async def get_document(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get document details"""
    try:
        # Handle topic-based pseudo documents
        if doc_id.startswith("topic_"):
            topic_name = doc_id.replace("topic_", "").replace("_", " ")
            # Return a mock document response for topic-based flashcards
            document_data = {
                "document_id": doc_id,
                "filename": f"{topic_name}.topic",
                "file_type": "topic",
                "file_size": 0,
                "processing_status": "completed",
                "processed_at": datetime.now(timezone.utc).isoformat() + "Z",
                "created_at": datetime.now(timezone.utc).isoformat() + "Z",
                "chunk_count": 0,
                "error_message": None,
                "is_topic_based": True,
                "topic_name": topic_name
            }
            
            return DocumentAPIResponse(
                success=True,
                data=document_data,
                message="ดึงข้อมูลหัวข้อสำเร็จ",
                timestamp=datetime.now(timezone.utc).isoformat() + "Z"
            )
        
        # Handle regular documents
        document = await document_processor.get_document(doc_id, user_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="ไม่พบเอกสารที่ร้องขอ")
        
        # Return document without content for performance (unless specifically requested)
        document_data = {
            "document_id": document.id,
            "filename": document.filename,
            "file_type": document.fileType,
            "file_size": document.fileSize,
            "processing_status": document.status,
            "processed_at": document.updatedAt,
            "created_at": document.createdAt,
            "chunk_count": len(getattr(document, 'chunks', [])),
            "error_message": document.errorMessage,
            "is_topic_based": False
        }
        
        return DocumentAPIResponse(
            success=True,
            data=document_data,
            message="ดึงข้อมูลเอกสารสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงข้อมูลเอกสาร")

@router.delete("/{doc_id}", response_model=DocumentAPIResponse)
async def delete_document(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a document"""
    try:
        success = await document_processor.delete_document(doc_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="ไม่พบเอกสารที่จะลบ")
        
        return DocumentAPIResponse(
            success=True,
            data={"document_id": doc_id},
            message="ลบเอกสารสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการลบเอกสาร")

@router.post("/{doc_id}/process", response_model=DocumentAPIResponse)
async def reprocess_document(
    doc_id: str,
    request: DocumentProcessRequest = DocumentProcessRequest(),
    user_id: str = Depends(get_current_user_id)
):
    """Reprocess document with different parameters"""
    try:
        # Get document
        document = await document_processor.get_document(doc_id, user_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="ไม่พบเอกสารที่ร้องขอ")
        
        # Reprocess chunks with new parameters
        await document_processor._process_chunks(
            doc_id, 
            document.content, 
            request.chunk_size, 
            request.chunk_overlap
        )
        
        return DocumentAPIResponse(
            success=True,
            data={
                "document_id": doc_id,
                "status": "reprocessed",
                "chunk_size": request.chunk_size,
                "chunk_overlap": request.chunk_overlap
            },
            message="ประมวลผลเอกสารใหม่สำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing document: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการประมวลผลเอกสารใหม่")

@router.get("/{doc_id}/stats", response_model=DocumentAPIResponse)
async def get_document_stats(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get document statistics"""
    try:
        stats = await document_processor.get_document_stats(doc_id, user_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="ไม่พบเอกสารที่ร้องขอ")
        
        return DocumentAPIResponse(
            success=True,
            data=stats,
            message="ดึงสถิติเอกสารสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงสถิติเอกสาร")

@router.post("/{doc_id}/search", response_model=DocumentAPIResponse)
async def search_document(
    doc_id: str,
    query: str = Form(...),
    top_k: int = Form(5),
    user_id: str = Depends(get_current_user_id)
):
    """Search within document content"""
    try:
        results = await document_processor.search_document_chunks(
            doc_id, query, user_id, top_k
        )
        
        return DocumentAPIResponse(
            success=True,
            data={
                "query": query,
                "results": results,
                "total_results": len(results)
            },
            message="ค้นหาในเอกสารสำเร็จ",
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error searching document: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการค้นหา")