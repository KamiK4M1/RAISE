import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from app.core.database import get_prisma_client
from app.models.document import DocumentModel, DocumentChunk, DocumentCreate, DocumentUpdate
from app.utils.file_handler import file_handler
from app.core.embeddings import embedding_service
from app.core.exceptions import DocumentProcessingError, DatabaseError
from app.utils.thai_processing import thai_processor

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Temporary cache for document chunks (could be Redis in production)
        self._document_chunks_cache: Dict[str, List[DocumentChunk]] = {}

    async def process_document(
        self, 
        file_path: str, 
        filename: str, 
        file_type: str, 
        file_size: int, 
        user_id: str,
        title: str = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> str:
        """Process uploaded document and store in database"""
        
        try:
            # Extract text from file
            logger.info(f"Extracting text from {filename}")
            content = await file_handler.extract_text(file_path, file_type)
            
            if not content.strip():
                raise DocumentProcessingError("ไม่สามารถดึงเนื้อหาจากไฟล์ได้")
            
            # Create document record using Prisma
            prisma = await get_prisma_client()
            
            document_data = DocumentCreate(
                userId=user_id,
                title=title or filename,
                filename=filename,
                content=content,
                fileType=file_type,
                fileSize=file_size,
                uploadPath=file_path
            )
            
            # Save initial document record
            document = await prisma.document.create(
                data=document_data.model_dump()
            )
            
            # Process in background (chunk and embed)
            await self._process_chunks(document.id, content, chunk_size, chunk_overlap)
            
            return document.id
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            # Update document status to failed if document was created
            if 'document' in locals():
                await self._update_document_status(document.id, "failed", str(e))
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
            
            # Update document status to completed (chunks will be stored separately if needed)
            prisma = await get_prisma_client()
            await prisma.document.update(
                where={"id": document_id},
                data={
                    "status": "completed",
                    "updatedAt": datetime.utcnow()
                }
            )
            
            # Store chunks in memory/cache for now (could be separate model later)
            # This maintains compatibility with existing search functionality
            self._document_chunks_cache[document_id] = document_chunks
            
            logger.info(f"Document {document_id} processed successfully with {len(document_chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Chunk processing error: {e}")
            await self._update_document_status(document_id, "failed", str(e))
            raise

    async def _update_document_status(self, document_id: str, status: str, error_message: str = None):
        """Update document processing status"""
        try:
            prisma = await get_prisma_client()
            update_data = {
                "status": status,
                "updatedAt": datetime.utcnow()
            }
            
            await prisma.document.update(
                where={"id": document_id},
                data=update_data
            )
            
        except Exception as e:
            logger.error(f"Error updating document status: {e}")

    async def get_document(self, document_id: str, user_id: str) -> Optional[DocumentModel]:
        """Get document by ID and user ID"""
        try:
            prisma = await get_prisma_client()
            document = await prisma.document.find_unique(
                where={"id": document_id},
                include={"user": False}  # Only get document data
            )
            
            if document and document.userId == user_id:
                # Convert to our model format 
                doc_dict = {
                    "id": document.id,
                    "userId": document.userId, 
                    "title": document.title,
                    "filename": document.filename,
                    "content": document.content,
                    "fileType": document.fileType,
                    "fileSize": document.fileSize,
                    "uploadPath": document.uploadPath,
                    "status": document.status,
                    "createdAt": document.createdAt,
                    "updatedAt": document.updatedAt
                }
                
                doc_data = DocumentModel.model_validate(doc_dict)
                return doc_data
            return None
            
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการดึงข้อมูลเอกสาร: {str(e)}")

    async def list_user_documents(self, user_id: str, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """List documents for a user"""
        try:
            prisma = await get_prisma_client()
            documents = await prisma.document.find_many(
                where={"userId": user_id},
                skip=skip,
                take=limit,
                order_by={"createdAt": "desc"}
            )
            
            doc_summaries = []
            for doc in documents:
                # Create summary without heavy content
                doc_summary = {
                    "document_id": doc.id,
                    "title": doc.title,
                    "filename": doc.filename,
                    "file_type": doc.fileType,
                    "file_size": doc.fileSize,
                    "processing_status": doc.status,
                    "created_at": doc.createdAt,
                    "updated_at": doc.updatedAt,
                    "chunk_count": len(self._document_chunks_cache.get(doc.id, []))
                }
                doc_summaries.append(doc_summary)
            
            return doc_summaries
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise DatabaseError(f"เกิดข้อผิดพลาดในการดึงรายการเอกสาร: {str(e)}")

    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete document and associated file"""
        try:
            prisma = await get_prisma_client()
            
            # Get document first to verify ownership and get file path
            document = await prisma.document.find_unique(
                where={"id": document_id}
            )
            
            if not document or document.userId != user_id:
                return False
            
            # Delete file
            if document.uploadPath:
                await file_handler.delete_file(document.uploadPath)
            
            # Delete document record
            await prisma.document.delete(
                where={"id": document_id}
            )
            
            # Clear from cache
            if document_id in self._document_chunks_cache:
                del self._document_chunks_cache[document_id]
            
            return True
            
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
            # Get document chunks from cache
            if document_id not in self._document_chunks_cache:
                # Try to get document to verify access
                document = await self.get_document(document_id, user_id)
                if not document:
                    return []
                # No chunks available
                return []
            
            document_chunks = self._document_chunks_cache[document_id]
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_single_embedding(query)
            
            # Get chunk embeddings
            chunk_embeddings = [chunk.embedding for chunk in document_chunks]
            
            # Find similar chunks
            similar_chunks = await embedding_service.find_most_similar(
                query_embedding, chunk_embeddings, top_k
            )
            
            # Return chunk data with similarity scores
            results = []
            for result in similar_chunks:
                chunk_index = result['index']
                chunk = document_chunks[chunk_index]
                results.append({
                    'text': chunk.text,
                    'chunk_index': chunk.chunkIndex,
                    'similarity': result['similarity']
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching document chunks: {e}")
            return []

    async def get_document_stats(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """Get document statistics"""
        try:
            prisma = await get_prisma_client()
            document = await prisma.document.find_unique(
                where={"id": document_id}
            )
            
            if not document or document.userId != user_id:
                return {}
            
            chunk_count = len(self._document_chunks_cache.get(document_id, []))
            
            stats = {
                "title": document.title,
                "filename": document.filename,
                "file_size": document.fileSize,
                "content_length": len(document.content),
                "chunk_count": chunk_count,
                "word_count": thai_processor.count_words(document.content),
                "thai_char_count": thai_processor.count_thai_characters(document.content),
                "language": thai_processor.detect_language(document.content),
                "processing_status": document.status,
                "created_at": document.createdAt,
                "updated_at": document.updatedAt
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