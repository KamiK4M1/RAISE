"""
Pydantic Schemas for the RAISE Learning Platform.
"""
from pydantic import BaseModel, Field, HttpUrl
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
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        schema.update(type="string")
        return schema

# --- Document Schemas ---
class DocumentModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    file_name: str
    s3_url: str  # Changed to str for simplicity, can be HttpUrl if validated
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: PyObjectId
    status: str = "processing"  # processing, completed, failed

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class DocumentListResponse(BaseModel):
    id: str
    file_name: str
    uploaded_at: datetime
    status: str

class DocumentProcessRequest(BaseModel):
    document_id: str