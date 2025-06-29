import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from app.database.mongodb import get_documents_collection
from app.models.document import DocumentModel, DocumentChunk
from app.utils.file_handler import file_handler
from app.core.embeddings import embedding_service
from app.core.exceptions import DocumentProcessingError, DatabaseError
from app.utils.thai_processing import thai_processor

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        pass

    async def process_document(
        self, 
        file_path: str, 
        filename: str, 
        file_type: str, 
        file_size: int, 
        user_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> str:
        """Process uploaded document and store in database"""
        document_id = str(uuid.uuid4())
        
        try:
            # Extract text from file
            logger.info(f"Extracting text from {filename}")
            content = await file_handler.extract_text(file_path, file_type)
            
            if not content.strip():
                raise DocumentProcessingError("ไม่สามารถดึงเนื้อหาจากไฟล์ได้")
            
            # Create document record
            document = DocumentModel(
                document_id=document_id,
                user_id=user_id,
                filename=filename,
                content=content,
                file_type=file_type,
                file_size=file_size,
                upload_path=file_path,
                processing_status="processing",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save initial document record
            collection = await get_documents_collection()
            await collection.insert_one(document.dict(by_alias=True, exclude={"id"}))
            
            # Process in background (chunk and embed)
            await self._process_chunks(document_id, content, chunk_size, chunk_overlap)
            
            return document_id
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            # Update document status to failed
            await self._update_document_status(document_id, "failed", str(e))
            raise DocumentProcessingError(f"เกิดข้อผิดพลาดในการประมวลผลเอกสาร: {str(e)}")

    async def _process_chunks(self, document_id: str, content: str, chunk_size: int, chunk_overlap: int):
        """Process document chunks and generate embeddings"""
        try:
            # Split text into chunks
            logger.info(f"Chunking document {document_id}")
            chunks = file_handler.chunk_text(content, chunk_size, chunk_overlap)
            
            if not chunks:
                raise DocumentProcessingError("ไม่สามารถแบ่งเนื้อหาเป็นส่วนย่อยได้")
            
            # Generate embeddings for chunks
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings(chunk_texts)
            
            # Create chunk objects with embeddings
            document_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                document_chunk = DocumentChunk(
                    text=chunk['text'],
                    embedding=embedding,
                    chunk_index=i
                )
                document_chunks.append(document_chunk)
            
            # Update document with chunks
            collection = await get_documents_collection()
            await collection.update_one(
                {"document_id": document_id},
                {
                    "$set": {
                        "chunks": [chunk.dict() for chunk in document_chunks],
                        "processing_status": "completed",
                        "processed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Document {document_id} processed successfully with {len(document_chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Chunk processing error: {e}")
            await self._update_document_status(document_id, "failed", str(e))
            raise

    async def _update_document_status(self, document_id: str, status: str, error_message: str = None):
        """Update document processing status"""
        try:
            collection = await get_documents_collection()
            update_data = {
                "processing_status": status,
                "updated_at": datetime.utcnow()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            await collection.update_one(
                {"document_id": document_id},
                {"$set": update_data}
            )
            
        except Exception as e:
            logger.error(f"Error updating document status: {e}")

    async def get_document(self, document_id: str, user_id: str) -> Optional[DocumentModel]:
        """Get document by ID and user ID"""
        try:
            collection = await get_documents_collection()
            document_data = await collection.find_one({
                "document_id": document_id,
                "user_id": user_id
            })
            
            if document_data:
                return DocumentModel(**document_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการดึงข้อมูลเอกสาร: {str(e)}")

    async def list_user_documents(self, user_id: str, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """List documents for a user"""
        try:
            collection = await get_documents_collection()
            cursor = collection.find({"user_id": user_id})
            cursor = cursor.skip(skip).limit(limit).sort("created_at", -1)
            
            documents = []
            async for doc in cursor:
                # Remove content and chunks from list view for performance
                doc_summary = {
                    "document_id": doc["document_id"],
                    "filename": doc["filename"],
                    "file_type": doc["file_type"],
                    "file_size": doc["file_size"],
                    "processing_status": doc["processing_status"],
                    "processed_at": doc.get("processed_at"),
                    "created_at": doc["created_at"],
                    "chunk_count": len(doc.get("chunks", []))
                }
                documents.append(doc_summary)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการดึงรายการเอกสาร: {str(e)}")

    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete document and associated file"""
        try:
            collection = await get_documents_collection()
            
            # Get document first to get file path
            document = await collection.find_one({
                "document_id": document_id,
                "user_id": user_id
            })
            
            if not document:
                return False
            
            # Delete file
            if document.get("upload_path"):
                await file_handler.delete_file(document["upload_path"])
            
            # Delete document record
            result = await collection.delete_one({
                "document_id": document_id,
                "user_id": user_id
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการลบเอกสาร: {str(e)}")

    async def search_document_chunks(
        self, 
        document_id: str, 
        query: str, 
        user_id: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant chunks in a document"""
        try:
            # Get document
            document = await self.get_document(document_id, user_id)
            if not document or not document.chunks:
                return []
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_single_embedding(query)
            
            # Get chunk embeddings
            chunk_embeddings = [chunk.embedding for chunk in document.chunks]
            
            # Find similar chunks
            similar_chunks = await embedding_service.find_most_similar(
                query_embedding, chunk_embeddings, top_k
            )
            
            # Return chunk data with similarity scores
            results = []
            for result in similar_chunks:
                chunk_index = result['index']
                chunk = document.chunks[chunk_index]
                results.append({
                    'text': chunk.text,
                    'chunk_index': chunk.chunk_index,
                    'similarity': result['similarity']
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching document chunks: {e}")
            return []

    async def get_document_stats(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """Get document statistics"""
        try:
            document = await self.get_document(document_id, user_id)
            if not document:
                return {}
            
            stats = {
                "filename": document.filename,
                "file_size": document.file_size,
                "content_length": len(document.content),
                "chunk_count": len(document.chunks),
                "word_count": thai_processor.count_words(document.content),
                "thai_char_count": thai_processor.count_thai_characters(document.content),
                "language": thai_processor.detect_language(document.content),
                "processing_status": document.processing_status,
                "created_at": document.created_at,
                "processed_at": document.processed_at
            }
            
            # Extract keywords
            keywords = thai_processor.extract_keywords(document.content)
            stats["keywords"] = keywords
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            return {}

# Global instance
document_processor = DocumentProcessor()