from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from datetime import datetime

class DocumentChunk(BaseModel):
    """Document chunk for text processing"""
    text: str
    embedding: List[float]
    chunkIndex: int
    pageNumber: Optional[int] = None

class DocumentModel(BaseModel):
    """Document model matching Prisma schema"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    id: str = Field(..., description="Document ID")
    userId: str = Field(..., description="User ID who owns the document")
    title: str = Field(..., description="Document title")
    filename: str = Field(..., description="Original filename")
    content: str = Field(..., description="Document content")
    fileType: str = Field(..., description="File type")
    fileSize: int = Field(..., description="File size in bytes")
    uploadPath: Optional[str] = Field(None, description="Upload path")
    status: str = Field(default="processing", description="Processing status")
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
    userId: str
    title: str
    filename: str
    content: str
    fileType: str
    fileSize: int
    uploadPath: Optional[str] = None
    
class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None