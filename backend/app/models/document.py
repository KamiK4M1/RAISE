from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from datetime import datetime

class DocumentChunk(BaseModel):
    """Document chunk for text processing"""
    id: Optional[str] = None
    document_id: str
    text: str
    embedding: List[float]
    chunkIndex: int
    startPos: Optional[int] = None
    endPos: Optional[int] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class DocumentChunkCreate(BaseModel):
    """Schema for creating document chunks"""
    chunk_index: int
    text: str
    embedding: List[float]
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None

class DocumentModel(BaseModel):
    """Alias for Document model (deprecated, use Document)"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    id: str = Field(..., description="Document ID")
    user_id: str = Field(..., description="User ID who owns the document")
    title: str = Field(..., description="Document title")
    filename: str = Field(..., description="Original filename")
    content: str = Field(..., description="Document content")
    fileType: str = Field(..., description="File type")
    fileSize: int = Field(..., description="File size in bytes")
    uploadPath: Optional[str] = Field(None, description="Upload path")
    status: str = Field(default="processing", description="Processing status")
    processingProgress: int = Field(default=0, description="Processing progress 0-100")
    errorMessage: Optional[str] = Field(None, description="Error message if processing failed")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class DocumentUpload(BaseModel):
    """Document upload request"""
    filename: str
    fileType: str
    fileSize: int
    title: Optional[str] = None

class DocumentResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str
    timestamp: str

class DocumentListResponse(BaseModel):
    success: bool
    data: List[dict]
    message: str
    timestamp: str

class DocumentProcessRequest(BaseModel):
    """Document processing configuration"""
    chunkSize: Optional[int] = 1000
    chunkOverlap: Optional[int] = 200
    
class DocumentCreate(BaseModel):
    """Schema for creating a new document"""
    title: str
    filename: str
    content: str
    file_type: str
    file_size: int
    upload_path: Optional[str] = None

class DocumentResponse(BaseModel):
    """Document response model"""
    id: str
    user_id: str
    title: str
    filename: str
    content: str
    fileType: str
    fileSize: int
    uploadPath: Optional[str]
    status: str
    processingProgress: int
    errorMessage: Optional[str]
    createdAt: datetime
    updatedAt: datetime
    
class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None