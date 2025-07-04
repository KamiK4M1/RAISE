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
            
            # Clean up the processed file from uploads folder
            try:
                # Get the document to retrieve the file path
                document = await documents_collection.find_one({"_id": ObjectId(doc_id)})
                if document and document.get("uploadPath"):
                    file_path = document["uploadPath"]
                    await file_handler.delete_file(file_path)
                    logger.info(f"Successfully deleted processed file: {file_path}")
            except Exception as cleanup_error:
                # Don't fail the processing if cleanup fails, just log it
                logger.warning(f"Failed to cleanup file for doc {doc_id}: {cleanup_error}")

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

    async def retrieve_document_chunks(
        self, 
        doc_id: str, 
        query: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve document chunks, optionally filtered by similarity to query"""
        try:
            chunks_collection = mongodb_manager.get_document_chunks_collection()
            
            if query:
                # Use semantic search to find relevant chunks
                from app.services.rag_service import get_rag_service
                rag_service = get_rag_service()
                
                # Use the new MongoDB vector search method
                results = await rag_service.vector_search_mongodb_rag(
                    query=query,
                    top_k=top_k,
                    document_id=doc_id
                )
                return results
            else:
                # Return all chunks for the document
                cursor = chunks_collection.find({"document_id": doc_id}).sort("chunk_index", 1)
                chunks = await cursor.to_list(length=None)
                return chunks
                
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {e}")
            return []

    async def search_across_documents(
        self,
        user_id: str,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search across multiple user documents using enhanced RAG capabilities"""
        try:
            from app.services.rag_service import get_rag_service
            rag_service = get_rag_service()
            
            # Get user's documents if not specified
            if not document_ids:
                documents_collection = mongodb_manager.get_documents_collection()
                user_docs = await documents_collection.find(
                    {"userId": user_id, "status": "completed"}
                ).to_list(length=100)
                document_ids = [str(doc["_id"]) for doc in user_docs]
            
            # Perform semantic search across documents
            chunks = await rag_service.semantic_search(
                query=query,
                user_id=user_id,
                document_ids=document_ids,
                top_k=top_k
            )
            
            # Convert RetrievedChunk objects to dictionaries
            results = []
            for chunk in chunks:
                results.append({
                    "text": chunk.text,
                    "similarity_score": chunk.similarity_score,
                    "document_id": chunk.document_id,
                    "document_title": chunk.document_title,
                    "chunk_index": chunk.chunk_index,
                    "confidence_level": chunk.confidence_level.value
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching across documents: {e}")
            return []

    async def get_document_context(
        self,
        doc_id: str,
        query: str,
        max_chunks: int = 5
    ) -> str:
        """Get contextual information from a document based on a query"""
        try:
            from app.services.rag_service import get_rag_service
            rag_service = get_rag_service()
            
            # Use the enhanced context retrieval method
            context = await rag_service.retrieve_context_advanced(
                query=query,
                top_k=max_chunks,
                document_id=doc_id
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting document context: {e}")
            return ""

    async def hybrid_document_search(
        self,
        user_id: str,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search (text + vector) across documents"""
        try:
            from app.services.rag_service import get_rag_service
            rag_service = get_rag_service()
            
            # Get user's documents if not specified
            if not document_ids:
                documents_collection = mongodb_manager.get_documents_collection()
                user_docs = await documents_collection.find(
                    {"userId": user_id, "status": "completed"}
                ).to_list(length=100)
                document_ids = [str(doc["_id"]) for doc in user_docs]
            
            # Perform hybrid search for each document and combine results
            all_results = []
            for doc_id in document_ids:
                results = await rag_service.hybrid_search_mongodb(
                    query=query,
                    top_k=top_k,
                    document_id=doc_id
                )
                all_results.extend(results)
            
            # Sort by combined score and return top results
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            return all_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in hybrid document search: {e}")
            return []

document_processor = DocumentProcessorService()