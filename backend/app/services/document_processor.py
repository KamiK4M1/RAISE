"""
Service for processing uploaded documents, including text extraction,
chunking, embedding generation, and storage.
This version is updated to use motor for direct MongoDB interaction.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import asyncio
from bson import ObjectId

from app.database.mongodb import mongodb_manager
from app.utils.file_handler import file_handler
from app.core.embeddings import embedding_service
from app.core.exceptions import DocumentProcessingError
from app.models.document import DocumentModel, DocumentChunk

logger = logging.getLogger(__name__)

class DocumentProcessorService:
    def __init__(self):
        self._document_chunks_cache: Dict[str, List[DocumentChunk]] = {}

    async def process_document(
        self,
        file_path: str,
        filename: str,
        file_type: str,
        file_size: int,
        user_id: str,
        title: str,
    ) -> str:
        """Process an uploaded document and store it in the database."""
        try:
            # Extract content
            content = await file_handler.extract_text(file_path, file_type)

            # Create document in MongoDB
            documents_collection = mongodb_manager.get_documents_collection()
            document_data = {
                "userId": user_id,
                "title": title,
                "filename": filename,
                "content": content,
                "fileType": file_type,
                "fileSize": file_size,
                "uploadPath": file_path,
                "status": "processing",
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
            }
            result = await documents_collection.insert_one(document_data)
            doc_id = str(result.inserted_id)

            # Process chunks in the background
            asyncio.create_task(self._process_chunks(doc_id, content))

            return doc_id
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise DocumentProcessingError(str(e))

    async def _process_chunks(
        self,
        doc_id: str,
        content: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """Chunk the document, generate embeddings, and store them."""
        try:
            # Chunk text
            chunks_data = file_handler.chunk_text(content, chunk_size, chunk_overlap)
            if not chunks_data:
                await self.update_document_status(doc_id, "completed", "No content to process")
                return

            # Generate embeddings
            texts_to_embed = [chunk['text'] for chunk in chunks_data]
            embeddings = await embedding_service.generate_embeddings(texts_to_embed)

            # Create DocumentChunk objects
            document_chunks = []
            for i, chunk_data in enumerate(chunks_data):
                chunk = DocumentChunk(
                    document_id=doc_id,
                    text=chunk_data['text'],
                    embedding=embeddings[i],
                    chunkIndex=chunk_data['chunk_index']
                )
                document_chunks.append(chunk)

            # Store chunks in cache and database
            self._document_chunks_cache[doc_id] = document_chunks
            chunks_collection = mongodb_manager.get_document_chunks_collection()
            
            # Convert chunks to database format
            chunk_documents = []
            for chunk in document_chunks:
                chunk_doc = {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunkIndex,
                    "text": chunk.text,
                    "embedding": chunk.embedding,
                    "start_pos": chunk.startPos,
                    "end_pos": chunk.endPos,
                    "created_at": chunk.createdAt
                }
                chunk_documents.append(chunk_doc)
            
            await chunks_collection.insert_many(chunk_documents)


            # Update document with chunks and status
            documents_collection = mongodb_manager.get_documents_collection()
            await documents_collection.update_one(
                {"_id": ObjectId(doc_id)},
                {
                    "$set": {
                        "status": "completed",
                        "updatedAt": datetime.now(timezone.utc),
                    }
                },
            )

        except Exception as e:
            logger.error(f"Error processing chunks for doc {doc_id}: {e}")
            await self.update_document_status(doc_id, "failed", str(e))

    async def get_document(self, doc_id: str, user_id: str) -> Optional[DocumentModel]:
        """Get a document by its ID."""
        documents_collection = mongodb_manager.get_documents_collection()
        doc_data = await documents_collection.find_one({"_id": ObjectId(doc_id), "userId": user_id})
        if doc_data:
            # Transform field names to match DocumentModel
            doc_data["id"] = str(doc_data["_id"])
            doc_data["user_id"] = doc_data.pop("userId")
            del doc_data["_id"]
            return DocumentModel(**doc_data)
        return None

    async def list_user_documents(self, user_id: str, skip: int, limit: int) -> List[Dict[str, Any]]:
        """List documents for a specific user."""
        documents_collection = mongodb_manager.get_documents_collection()
        cursor = documents_collection.find({"userId": user_id}).skip(skip).limit(limit)
        
        documents = []
        async for doc in cursor:
            # Transform MongoDB document to serializable format
            doc_data = {
                "document_id": str(doc["_id"]),
                "user_id": doc["userId"],
                "title": doc.get("title", ""),
                "filename": doc.get("filename", ""),
                "file_type": doc.get("fileType", ""),
                "file_size": doc.get("fileSize", 0),
                "status": doc.get("status", "processing"),
                "processing_progress": doc.get("processingProgress", 0),
                "error_message": doc.get("errorMessage"),
                "created_at": doc.get("createdAt"),
                "updated_at": doc.get("updatedAt")
            }
            documents.append(doc_data)
        
        return documents

    async def delete_document(self, doc_id: str, user_id: str) -> bool:
        """Delete a document and its associated chunks."""
        documents_collection = mongodb_manager.get_documents_collection()
        result = await documents_collection.delete_one({"_id": ObjectId(doc_id), "userId": user_id})

        if result.deleted_count > 0:
            chunks_collection = mongodb_manager.get_document_chunks_collection()
            await chunks_collection.delete_many({"document_id": doc_id})
            if doc_id in self._document_chunks_cache:
                del self._document_chunks_cache[doc_id]
            return True
        return False

    async def update_document_status(self, doc_id: str, status: str, error_message: Optional[str] = None):
        """Update the processing status of a document."""
        documents_collection = mongodb_manager.get_documents_collection()
        update_data = {"status": status, "updatedAt": datetime.now(timezone.utc)}
        if error_message:
            update_data["error_message"] = error_message
        await documents_collection.update_one({"_id": ObjectId(doc_id)}, {"$set": update_data})

document_processor = DocumentProcessorService()