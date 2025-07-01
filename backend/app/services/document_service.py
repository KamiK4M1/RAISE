"""
Document Service for RAISE Learning Platform using MongoDB

This service handles:
- Document upload and storage
- Document processing and chunking
- Document retrieval and management
- Document metadata handling
- Vector embeddings for document chunks
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from bson import ObjectId

from app.database.mongodb import (
    mongodb_manager, Collections,
    create_document_document, create_document_chunk_document
)
from app.models.document import (
    Document, DocumentCreate, DocumentResponse, DocumentUpdate,
    DocumentChunk, DocumentChunkCreate
)
from app.core.exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for handling document operations using MongoDB"""

    def __init__(self):
        self.documents_collection = mongodb_manager.get_documents_collection()
        self.chunks_collection = mongodb_manager.get_document_chunks_collection()

    async def create_document(self, user_id: str, document_data: DocumentCreate) -> DocumentResponse:
        """Create a new document"""
        try:
            # Create document
            document_dict = create_document_document(
                user_id=user_id,
                title=document_data.title,
                filename=document_data.filename,
                content=document_data.content,
                file_type=document_data.file_type,
                file_size=document_data.file_size,
                upload_path=document_data.upload_path
            )
            
            result = await self.documents_collection.insert_one(document_dict)
            document_id = str(result.inserted_id)
            
            # Retrieve the created document
            document = await self.documents_collection.find_one({"_id": result.inserted_id})
            
            # Convert for response
            document = self._convert_document_for_response(document)
            
            return DocumentResponse(**document)

        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating document"
            )

    async def get_document_by_id(self, document_id: str, user_id: str) -> DocumentResponse:
        """Get document by ID"""
        try:
            document = await self.documents_collection.find_one({
                "_id": ObjectId(document_id),
                "user_id": ObjectId(user_id)
            })
            
            if not document:
                raise DocumentNotFoundError
            
            document = self._convert_document_for_response(document)
            return DocumentResponse(**document)

        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving document"
            )

    async def get_user_documents(self, user_id: str, skip: int = 0, limit: int = 20) -> List[DocumentResponse]:
        """Get all documents for a user"""
        try:
            cursor = self.documents_collection.find(
                {"user_id": ObjectId(user_id)}
            ).sort("created_at", -1).skip(skip).limit(limit)
            
            documents = []
            async for doc in cursor:
                doc = self._convert_document_for_response(doc)
                documents.append(DocumentResponse(**doc))
            
            return documents

        except Exception as e:
            logger.error(f"Error retrieving user documents: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving documents"
            )

    async def update_document(self, document_id: str, user_id: str, update_data: DocumentUpdate) -> DocumentResponse:
        """Update document"""
        try:
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()

            updated_document = await self.documents_collection.find_one_and_update(
                {"_id": ObjectId(document_id), "user_id": ObjectId(user_id)},
                {"$set": update_dict},
                return_document=True
            )

            if not updated_document:
                raise DocumentNotFoundError

            updated_document = self._convert_document_for_response(updated_document)
            return DocumentResponse(**updated_document)

        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating document"
            )

    async def delete_document(self, document_id: str, user_id: str) -> Dict[str, str]:
        """Delete document and its chunks"""
        try:
            # Delete document chunks first
            await self.chunks_collection.delete_many({"document_id": ObjectId(document_id)})
            
            # Delete document
            result = await self.documents_collection.delete_one({
                "_id": ObjectId(document_id),
                "user_id": ObjectId(user_id)
            })

            if result.deleted_count == 0:
                raise DocumentNotFoundError

            return {"message": "Document deleted successfully"}

        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting document"
            )

    async def update_document_status(self, document_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update document processing status"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            result = await self.documents_collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error updating document status: {e}")
            return False

    async def create_document_chunks(self, document_id: str, chunks_data: List[DocumentChunkCreate]) -> List[str]:
        """Create document chunks with embeddings"""
        try:
            chunk_documents = []
            for chunk_data in chunks_data:
                chunk_dict = create_document_chunk_document(
                    document_id=document_id,
                    chunk_index=chunk_data.chunk_index,
                    text=chunk_data.text,
                    embedding=chunk_data.embedding,
                    start_pos=chunk_data.start_pos,
                    end_pos=chunk_data.end_pos
                )
                chunk_documents.append(chunk_dict)
            
            if chunk_documents:
                result = await self.chunks_collection.insert_many(chunk_documents)
                return [str(chunk_id) for chunk_id in result.inserted_ids]
            
            return []

        except Exception as e:
            logger.error(f"Error creating document chunks: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating document chunks"
            )

    async def get_document_chunks(self, document_id: str, skip: int = 0, limit: int = 50) -> List[DocumentChunk]:
        """Get document chunks"""
        try:
            cursor = self.chunks_collection.find(
                {"document_id": ObjectId(document_id)}
            ).sort("chunk_index", 1).skip(skip).limit(limit)
            
            chunks = []
            async for chunk in cursor:
                chunk = self._convert_chunk_for_response(chunk)
                chunks.append(DocumentChunk(**chunk))
            
            return chunks

        except Exception as e:
            logger.error(f"Error retrieving document chunks: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving document chunks"
            )

    async def search_documents(self, user_id: str, query: str, limit: int = 10) -> List[DocumentResponse]:
        """Search documents by text"""
        try:
            # Use MongoDB text search
            cursor = self.documents_collection.find(
                {
                    "$and": [
                        {"user_id": ObjectId(user_id)},
                        {"$text": {"$search": query}}
                    ]
                },
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            documents = []
            async for doc in cursor:
                doc = self._convert_document_for_response(doc)
                documents.append(DocumentResponse(**doc))
            
            return documents

        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error searching documents"
            )

    def _convert_document_for_response(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to response format"""
        document["id"] = str(document["_id"])
        del document["_id"]
        document["user_id"] = str(document["user_id"])
        document["createdAt"] = document.pop("created_at")
        document["updatedAt"] = document.pop("updated_at")
        document["fileType"] = document.pop("file_type")
        document["fileSize"] = document.pop("file_size")
        document["uploadPath"] = document.pop("upload_path", None)
        document["processingProgress"] = document.pop("processing_progress", 0)
        document["errorMessage"] = document.pop("error_message", None)
        return document

    def _convert_chunk_for_response(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB chunk to response format"""
        chunk["id"] = str(chunk["_id"])
        del chunk["_id"]
        chunk["document_id"] = str(chunk["document_id"])
        chunk["chunkIndex"] = chunk.pop("chunk_index")
        chunk["startPos"] = chunk.pop("start_pos", None)
        chunk["endPos"] = chunk.pop("end_pos", None)
        chunk["createdAt"] = chunk.pop("created_at")
        return chunk

# Global document service instance
document_service = DocumentService()