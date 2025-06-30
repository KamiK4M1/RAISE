import uuid
import os
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import logging
import aiohttp
import aiofiles
from pathlib import Path

from app.core.database import get_prisma_client
from app.models.document import DocumentModel, DocumentChunk, DocumentCreate, DocumentUpdate
from app.utils.file_handler import file_handler
from app.core.embeddings import embedding_service
from app.core.exceptions import DocumentProcessingError, DatabaseError
from app.utils.thai_processing import thai_processor
from app.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Temporary cache for document chunks (could be Redis in production)
        self._document_chunks_cache: Dict[str, List[DocumentChunk]] = {}
        
        # LlamaParse configuration
        self.llamaparse_api_key = settings.llamaparse_api_key
        self.llamaparse_base_url = "https://api.cloud.llamaindex.ai/api/parsing"
        
        # Progress tracking for frontend updates
        self._processing_status: Dict[str, Dict[str, Any]] = {}
        
        if not self.llamaparse_api_key:
            logger.warning("LlamaParse API key not configured - falling back to basic text extraction")

    async def process_document(
        self, 
        file_path: str, 
        filename: str, 
        file_type: str, 
        file_size: int, 
        user_id: str,
        title: str = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        progress_callback: Optional[Callable[[str, float, str], None]] = None
    ) -> str:
        """Process uploaded document with AI pipeline and store in database"""
        
        document_id = None
        try:
            # Initialize progress tracking
            process_id = str(uuid.uuid4())
            self._processing_status[process_id] = {
                "status": "starting",
                "progress": 0.0,
                "message": "@#4H!I2##0!'%%@-*2#",
                "document_id": None
            }
            
            if progress_callback:
                progress_callback(process_id, 0.0, "@#4H!I2##0!'%%@-*2#")
            
            # Create initial document record
            prisma = await get_prisma_client()
            
            document_data = DocumentCreate(
                userId=user_id,
                title=title or filename,
                filename=filename,
                content="",  # Will be filled after extraction
                fileType=file_type,
                fileSize=file_size,
                uploadPath=file_path
            )
            
            document = await prisma.document.create(
                data=document_data.model_dump()
            )
            document_id = document.id
            
            self._processing_status[process_id]["document_id"] = document_id
            
            # Step 1: Extract text using LlamaParse or fallback methods
            self._update_progress(process_id, 10.0, "3%16I-'2!2@-*2#", progress_callback)
            content = await self._extract_text_with_llamaparse(file_path, file_type, filename)
            
            if not content.strip():
                raise DocumentProcessingError("D!H*2!2#6@7I-+22D%LDI")
            
            # Update document with extracted content
            await prisma.document.update(
                where={"id": document_id},
                data={"content": content}
            )
            
            # Step 2: Process chunks and embeddings
            self._update_progress(process_id, 30.0, "3%1AH@-*2#@G*H'"H-"", progress_callback)
            await self._process_chunks_with_ai(document_id, content, chunk_size, chunk_overlap, process_id, progress_callback)
            
            # Step 3: Complete processing
            self._update_progress(process_id, 100.0, "#0!'%%@-*2#@*#G*4I", progress_callback)
            
            # Clean up progress tracking
            if process_id in self._processing_status:
                del self._processing_status[process_id]
            
            return document_id
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            
            # Update document status to failed if document was created
            if document_id:
                await self._update_document_status(document_id, "failed", str(e))
            
            if progress_callback:
                progress_callback(process_id, 0.0, f"I-4%2: {str(e)}")
                
            raise DocumentProcessingError(f"@4I-4%2C2##0!'%%@-*2#: {str(e)}")

    async def _extract_text_with_llamaparse(
        self, 
        file_path: str, 
        file_type: str, 
        filename: str
    ) -> str:
        """Extract text using LlamaParse API with fallback to basic extraction"""
        
        # Try LlamaParse first for supported formats
        if self.llamaparse_api_key and file_type.lower() in ['pdf', 'docx']:
            try:
                logger.info(f"Using LlamaParse for {filename}")
                content = await self._llamaparse_extract(file_path, filename)
                if content and content.strip():
                    logger.info(f"LlamaParse extraction successful for {filename}")
                    return content
            except Exception as e:
                logger.warning(f"LlamaParse extraction failed for {filename}: {e}")
        
        # Fallback to basic extraction
        logger.info(f"Using fallback extraction for {filename}")
        return await self._basic_text_extraction(file_path, file_type)
    
    async def _llamaparse_extract(self, file_path: str, filename: str) -> str:
        """Extract text using LlamaParse API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.llamaparse_api_key}"
            }
            
            # Read file content
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            data.add_field('file', file_content, filename=filename)
            data.add_field('language', 'auto')  # Auto-detect language
            data.add_field('parsing_instruction', 'Extract all text content including tables, headers, and formatting. Preserve Thai and English text accurately.')
            
            async with aiohttp.ClientSession() as session:
                # Submit parsing job
                async with session.post(
                    f"{self.llamaparse_base_url}/upload",
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise DocumentProcessingError(f"LlamaParse upload failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    job_id = result.get('id')
                    
                    if not job_id:
                        raise DocumentProcessingError("LlamaParse did not return job ID")
                
                # Poll for completion
                max_attempts = 30  # 5 minutes max wait
                for attempt in range(max_attempts):
                    await asyncio.sleep(10)  # Wait 10 seconds between checks
                    
                    async with session.get(
                        f"{self.llamaparse_base_url}/job/{job_id}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as status_response:
                        if status_response.status != 200:
                            continue
                        
                        status_result = await status_response.json()
                        status = status_result.get('status')
                        
                        if status == 'SUCCESS':
                            # Get the parsed content
                            content = status_result.get('result', {}).get('markdown', '')
                            if content:
                                return self._clean_llamaparse_content(content)
                            else:
                                raise DocumentProcessingError("LlamaParse returned empty content")
                        
                        elif status == 'ERROR':
                            error_msg = status_result.get('error', 'Unknown error')
                            raise DocumentProcessingError(f"LlamaParse processing failed: {error_msg}")
                        
                        # Status is still PENDING, continue polling
                
                raise DocumentProcessingError("LlamaParse processing timeout")
                
        except aiohttp.ClientError as e:
            raise DocumentProcessingError(f"LlamaParse API connection error: {str(e)}")
        except Exception as e:
            raise DocumentProcessingError(f"LlamaParse extraction error: {str(e)}")
    
    def _clean_llamaparse_content(self, content: str) -> str:
        """Clean and normalize LlamaParse extracted content"""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        # Clean up markdown artifacts if needed
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        
        # Use Thai processor for final cleaning
        return thai_processor.clean_thai_text(content)
    
    async def _basic_text_extraction(self, file_path: str, file_type: str) -> str:
        """Basic text extraction using existing file handler"""
        if file_type.lower() == 'pdf':
            return await file_handler.read_pdf(file_path)
        elif file_type.lower() == 'docx':
            return await file_handler.read_docx(file_path)
        elif file_type.lower() == 'txt':
            return await file_handler.read_txt(file_path)
        else:
            raise DocumentProcessingError(f"Unsupported file type: {file_type}")
    
    def _intelligent_chunking(
        self, 
        content: str, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """Intelligent text chunking with sentence boundary awareness"""
        
        # Clean and prepare text
        content = content.strip()
        if not content:
            return []
        
        # Split by paragraphs first
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        current_size = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            
            # If paragraph alone exceeds chunk size, split it
            if paragraph_size > chunk_size:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'chunk_index': chunk_index,
                        'size': len(current_chunk)
                    })
                    chunk_index += 1
                    current_chunk = ""
                    current_size = 0
                
                # Split long paragraph by sentences
                sentences = self._split_by_sentences(paragraph)
                temp_chunk = ""
                
                for sentence in sentences:
                    if len(temp_chunk) + len(sentence) + 1 <= chunk_size:
                        temp_chunk += sentence + " "
                    else:
                        if temp_chunk:
                            chunks.append({
                                'text': temp_chunk.strip(),
                                'chunk_index': chunk_index,
                                'size': len(temp_chunk)
                            })
                            chunk_index += 1
                        
                        # Start new chunk with overlap
                        if chunks and chunk_overlap > 0:
                            prev_text = chunks[-1]['text']
                            overlap_text = prev_text[-chunk_overlap:] if len(prev_text) > chunk_overlap else prev_text
                            temp_chunk = overlap_text + " " + sentence + " "
                        else:
                            temp_chunk = sentence + " "
                
                current_chunk = temp_chunk
                current_size = len(temp_chunk)
            
            # Normal paragraph processing
            elif current_size + paragraph_size + 2 <= chunk_size:  # +2 for \n\n
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                current_size = len(current_chunk)
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'chunk_index': chunk_index,
                        'size': len(current_chunk)
                    })
                    chunk_index += 1
                
                # Start new chunk with overlap
                if chunks and chunk_overlap > 0:
                    prev_text = chunks[-1]['text']
                    overlap_text = prev_text[-chunk_overlap:] if len(prev_text) > chunk_overlap else prev_text
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_size = len(current_chunk)
        
        # Add the last chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'chunk_index': chunk_index,
                'size': len(current_chunk)
            })
        
        logger.info(f"Created {len(chunks)} intelligent chunks")
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences, handling Thai and English"""
        # Simple sentence splitting - can be enhanced with more sophisticated NLP
        sentences = []
        
        # Split by common sentence endings
        parts = re.split(r'[.!?]\s+', text)
        
        for i, part in enumerate(parts):
            part = part.strip()
            if part:
                # Add back the punctuation except for the last part
                if i < len(parts) - 1:
                    # Determine what punctuation was used
                    remaining_text = text[text.find(part) + len(part):]
                    if remaining_text and remaining_text[0] in '.!?':
                        part += remaining_text[0]
                sentences.append(part)
        
        return sentences if sentences else [text]
    
    def _update_progress(
        self, 
        process_id: str, 
        progress: float, 
        message: str, 
        callback: Optional[Callable[[str, float, str], None]] = None
    ):
        """Update processing progress"""
        if process_id in self._processing_status:
            self._processing_status[process_id].update({
                "progress": progress,
                "message": message,
                "updated_at": datetime.utcnow()
            })
        
        if callback:
            callback(process_id, progress, message)
        
        logger.info(f"Progress {process_id}: {progress}% - {message}")
    
    async def _process_chunks_with_ai(
        self, 
        document_id: str, 
        content: str, 
        chunk_size: int, 
        chunk_overlap: int, 
        process_id: str,
        progress_callback: Optional[Callable[[str, float, str], None]] = None
    ):
        """Process document chunks with AI embeddings and enhanced error handling"""
        try:
            # Step 1: Intelligent chunking
            self._update_progress(process_id, 40.0, "3%1AHI-'2!-"H2
2	%2", progress_callback)
            chunks = self._intelligent_chunking(content, chunk_size, chunk_overlap)
            
            if not chunks:
                raise DocumentProcessingError("D!H*2!2#AH@7I-+2@G*H'"H-"DI")
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            
            # Step 2: Generate embeddings with batching
            self._update_progress(process_id, 50.0, f"3%1*#I2 embeddings *3+#1 {len(chunks)} *H'", progress_callback)
            
            # Process in batches to avoid overwhelming the API
            batch_size = 10
            all_embeddings = []
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                batch_texts = [chunk['text'] for chunk in batch_chunks]
                
                # Update progress for this batch
                batch_progress = 50.0 + (30.0 * (i + len(batch_chunks)) / len(chunks))
                self._update_progress(
                    process_id, 
                    batch_progress, 
                    f"3%1#0!'%% embeddings %8H!5H {i//batch_size + 1}", 
                    progress_callback
                )
                
                try:
                    batch_embeddings = await embedding_service.generate_embeddings(batch_texts)
                    all_embeddings.extend(batch_embeddings)
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                    # Generate zero embeddings as fallback
                    embedding_dim = embedding_service.get_embedding_dimension()
                    fallback_embeddings = [[0.0] * embedding_dim] * len(batch_texts)
                    all_embeddings.extend(fallback_embeddings)
            
            if len(all_embeddings) != len(chunks):
                raise DocumentProcessingError(f"Embedding count mismatch: {len(all_embeddings)} vs {len(chunks)}")
            
            # Step 3: Create document chunks with embeddings
            self._update_progress(process_id, 80.0, "3%11@GI-!9%*H'"H-"", progress_callback)
            
            document_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
                document_chunk = DocumentChunk(
                    text=chunk['text'],
                    embedding=embedding,
                    chunkIndex=i,  # Fixed attribute name
                    pageNumber=None  # Could be enhanced to track page numbers
                )
                document_chunks.append(document_chunk)
            
            # Step 4: Store chunks in database/cache with error handling
            self._update_progress(process_id, 90.0, "3%116I-!9%@-*2#", progress_callback)
            
            try:
                # Store in cache for immediate use
                self._document_chunks_cache[document_id] = document_chunks
                
                # Update document status to completed
                prisma = await get_prisma_client()
                await prisma.document.update(
                    where={"id": document_id},
                    data={
                        "status": "completed",
                        "updatedAt": datetime.utcnow()
                    }
                )
                
                logger.info(f"Document {document_id} processed successfully with {len(document_chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error storing document chunks: {e}")
                await self._update_document_status(document_id, "failed", f"Storage error: {str(e)}")
                raise
            
        except Exception as e:
            logger.error(f"Chunk processing error for document {document_id}: {e}")
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
            raise DatabaseError(f"@4I-4%2C2#6I-!9%@-*2#: {str(e)}")

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
            raise DatabaseError(f"@4I-4%2C2#6#2"2#@-*2#: {str(e)}")

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
            raise DatabaseError(f"@4I-4%2C2#%@-*2#: {str(e)}")

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

    def get_processing_status(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Get current processing status for a process"""
        return self._processing_status.get(process_id)
    
    async def cleanup_file(self, file_path: str):
        """Clean up uploaded file after processing"""
        try:
            if os.path.exists(file_path):
                await asyncio.to_thread(os.remove, file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")

# Global instance
document_processor = DocumentProcessor()