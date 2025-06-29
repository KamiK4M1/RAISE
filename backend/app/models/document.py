from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class DocumentChunk(BaseModel):
    text: str
    embedding: List[float]
    chunk_index: int
    page_number: Optional[int] = None

class DocumentModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    document_id: str
    user_id: str
    filename: str
    content: str
    chunks: List[DocumentChunk] = []
    processed_at: Optional[datetime] = None
    file_type: str
    file_size: int
    upload_path: str
    processing_status: str = "pending"  # pending, processing, completed, failed
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class DocumentUpload(BaseModel):
    filename: str
    file_type: str
    file_size: int

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
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200