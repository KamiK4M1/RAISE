"""
Service for processing uploaded documents, including text extraction,
chunking, embedding generation, and storage.
This version is updated to use motor for direct MongoDB interaction.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio

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
            documents_collection = mongodb_manager("documents")
            document_data = {
                "userId": user_id,
                "title": title,
                "filename": filename,
                "content": content,
                "fileType": file_type,
                "fileSize": file_size,
                "uploadPath": file_path,
                "status": "processing",
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow(),
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
                    text=chunk_data['text'],
                    embedding=embeddings[i],
                    chunkIndex=chunk_data['chunk_index']
                )
                document_chunks.append(chunk)

            # Store chunks in cache and database
            self._document_chunks_cache[doc_id] = document_chunks
            chunks_collection = mongodb_manager("chunks")
            await chunks_collection.insert_many([c.dict() for c in document_chunks])


            # Update document with chunks and status
            documents_collection = mongodb_manager("documents")
            await documents_collection.update_one(
                {"_id": doc_id},
                {
                    "$set": {
                        "status": "completed",
                        "updatedAt": datetime.utcnow(),
                    }
                },
            )

        except Exception as e:
            logger.error(f"Error processing chunks for doc {doc_id}: {e}")
            await self.update_document_status(doc_id, "failed", str(e))

    async def get_document(self, doc_id: str, user_id: str) -> Optional[DocumentModel]:
        """Get a document by its ID."""
        documents_collection = mongodb_manager("documents")
        doc_data = await documents_collection.find_one({"_id": doc_id, "userId": user_id})
        if doc_data:
            return DocumentModel(**doc_data)
        return None

    async def list_user_documents(self, user_id: str, skip: int, limit: int) -> List[Dict[str, Any]]:
        """List documents for a specific user."""
        documents_collection = mongodb_manager("documents")
        cursor = documents_collection.find({"userId": user_id}).skip(skip).limit(limit)
        return [doc async for doc in cursor]

    async def delete_document(self, doc_id: str, user_id: str) -> bool:
        """Delete a document and its associated chunks."""
        documents_collection = mongodb_manager("documents")
        result = await documents_collection.delete_one({"_id": doc_id, "userId": user_id})

        if result.deleted_count > 0:
            chunks_collection = mongodb_manager("chunks")
            await chunks_collection.delete_many({"document_id": doc_id})
            if doc_id in self._document_chunks_cache:
                del self._document_chunks_cache[doc_id]
            return True
        return False

    async def update_document_status(self, doc_id: str, status: str, error_message: Optional[str] = None):
        """Update the processing status of a document."""
        documents_collection = mongodb_manager("documents")
        update_data = {"status": status, "updatedAt": datetime.utcnow()}
        if error_message:
            update_data["error_message"] = error_message
        await documents_collection.update_one({"_id": doc_id}, {"$set": update_data})

document_processor = DocumentProcessorService()