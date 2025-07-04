import os
import asyncio
import logging
import aiohttp
import tiktoken
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic_settings import BaseSettings
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Settings ---
class Settings(BaseSettings):
    mongodb_uri: str = "mongodb+srv://admin:admin@cluster0.orptq.mongodb.net/raise_db?retryWrites=true&w=majority"
    database_name: str = "raise_db"
    collection_name: str = "document_chunks"
    vector_index_name: str = "vector_search_index"
    
    # BGE-M3 Embedding endpoint (required)
    embedding_endpoint_url: str = "https://kxm1k4m1-bge-m3.hf.space"
    hf_auth_token: Optional[str] = None

settings = Settings()

# --- Custom Exceptions ---
class EmbeddingError(Exception):
    """Custom exception for embedding service errors."""
    pass

class RAGError(Exception):
    """Custom exception for RAG system errors."""
    pass

# --- Embedding Service ---
class EmbeddingService:
    def __init__(self):
        self.embedding_endpoint = settings.embedding_endpoint_url
        if not self.embedding_endpoint:
            raise EmbeddingError("Embedding endpoint URL not configured")
        self.auth_token = settings.hf_auth_token
        logger.info(f"Initialized BGE-M3 embedding service: {self.embedding_endpoint}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of texts by calling the BGE-M3 API."""
        if not texts:
            return []
        
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        payload = {"texts": texts}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.embedding_endpoint}/api/embeddings",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise EmbeddingError(f"Embedding API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    if not result.get("success"):
                        raise EmbeddingError(f"Embedding API returned error: {result.get('error', 'Unknown error')}")
                    
                    embeddings = result.get("embeddings", [])
                    logger.info(f"Generated {len(embeddings)} embeddings using BGE-M3")
                    return embeddings
        except Exception as e:
            logger.error(f"BGE-M3 embedding generation error: {e}")
            raise EmbeddingError(f"Failed to get embedding: {str(e)}")

    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generates an embedding for a single text using BGE-M3."""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []

# --- Text Processing ---
class TextProcessor:
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Split text into chunks with overlap."""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            if i + chunk_size >= len(tokens):
                break
        
        return chunks

# --- MongoDB RAG System ---
class MongoDBRAG:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db[settings.collection_name]
        self.embedding_service = EmbeddingService()
        self.text_processor = TextProcessor()
        
        logger.info("MongoDB RAG system initialized")

    async def create_vector_index(self):
        """Create vector search index if it doesn't exist."""
        try:
            # List existing indexes
            indexes = await self.collection.list_indexes().to_list(length=None)
            index_names = [idx.get('name') for idx in indexes]
            
            if settings.vector_index_name not in index_names:
                logger.info(f"Vector index '{settings.vector_index_name}' needs to be created manually in MongoDB Atlas")
                logger.info("Index definition for BGE-M3 (1024 dimensions):")
                index_def = {
                    "fields": [
                        {
                            "numDimensions": 1024,  # BGE-M3 produces 1024-dimensional embeddings
                            "path": "embedding",
                            "similarity": "cosine",
                            "type": "vector"
                        }
                    ]
                }
                logger.info(index_def)
            else:
                logger.info(f"Vector index '{settings.vector_index_name}' already exists")
        except Exception as e:
            logger.warning(f"Could not check vector index: {e}")

    async def add_document(self, 
                          text: str, 
                          document_id: Optional[str] = None,
                          metadata: Dict[str, Any] = None,
                          chunk_size: int = 512,
                          overlap: int = 50) -> List[str]:
        """Add document to RAG system with chunking."""
        if metadata is None:
            metadata = {}
        
        metadata['created_at'] = datetime.utcnow()
        
        # Chunk the text
        chunks = self.text_processor.chunk_text(text, chunk_size, overlap)
        
        # Generate embeddings for chunks
        embeddings = await self.embedding_service.generate_embeddings(chunks)
        
        # Prepare documents
        documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc = {
                'text': chunk,
                'embedding': embedding,
                'metadata': {
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
            }
            if document_id:
                doc['document_id'] = document_id
            documents.append(doc)
        
        # Insert documents
        result = await self.collection.insert_many(documents)
        
        logger.info(f"Added {len(documents)} chunks for document_id: {document_id}")
        return [str(doc_id) for doc_id in result.inserted_ids]

    async def vector_search(self, 
                           query: str, 
                           top_k: int = 5, 
                           document_id: Optional[str] = None,
                           score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        logger.info(f"Searching for: '{query[:50]}...'")
        
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_single_embedding(query)
        if not query_embedding:
            logger.error("Could not generate embedding for search query")
            return []

        # Build vector search stage
        vector_search_stage = {
            "$vectorSearch": {
                "index": settings.vector_index_name,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": min(100, top_k * 10),
                "limit": top_k
            }
        }

        # Add document filter if specified
        if document_id:
            vector_search_stage["$vectorSearch"]["filter"] = {"document_id": document_id}

        # Add projection stage
        project_stage = {
            "$project": {
                "score": {"$meta": "vectorSearchScore"},
                "text": 1,
                "document_id": 1,
                "metadata": 1
            }
        }

        # Add score filtering if needed
        match_stage = None
        if score_threshold > 0:
            match_stage = {"$match": {"score": {"$gte": score_threshold}}}

        # Build pipeline
        pipeline = [vector_search_stage, project_stage]
        if match_stage:
            pipeline.append(match_stage)

        # Execute search
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=top_k)
        
        logger.info(f"Found {len(results)} similar documents")
        return results

    async def retrieve_context(self, query: str, top_k: int = 5, document_id: Optional[str] = None) -> str:
        """Retrieve relevant context for a query."""
        results = await self.vector_search(query, top_k, document_id)
        
        context_pieces = []
        for doc in results:
            # Include score in context for transparency
            score = doc.get('score', 0)
            text = doc.get('text', '')
            context_pieces.append(f"[Score: {score:.3f}] {text}")
        
        return '\n\n'.join(context_pieces)

    async def hybrid_search(self, 
                           query: str, 
                           top_k: int = 5,
                           document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform hybrid search (text + vector)."""
        # Text search using MongoDB text index
        text_results = []
        try:
            text_cursor = self.collection.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(top_k * 2)
            text_results = await text_cursor.to_list(length=top_k * 2)
        except Exception as e:
            logger.warning(f"Text search failed (no text index?): {e}")

        # Vector search
        vector_results = await self.vector_search(query, top_k * 2, document_id)

        # Combine and deduplicate results
        combined_results = {}
        
        # Add text results
        for doc in text_results:
            doc_id = str(doc['_id'])
            combined_results[doc_id] = {
                'document': doc,
                'text_score': doc.get('score', 0),
                'vector_score': 0
            }

        # Add vector results
        for doc in vector_results:
            doc_id = str(doc['_id'])
            if doc_id in combined_results:
                combined_results[doc_id]['vector_score'] = doc.get('score', 0)
            else:
                combined_results[doc_id] = {
                    'document': doc,
                    'text_score': 0,
                    'vector_score': doc.get('score', 0)
                }

        # Calculate combined scores (weighted average)
        text_weight = 0.3
        vector_weight = 0.7
        
        for doc_id, scores in combined_results.items():
            combined_score = (
                text_weight * scores['text_score'] + 
                vector_weight * scores['vector_score']
            )
            combined_results[doc_id]['combined_score'] = combined_score

        # Sort by combined score
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )

        return [item['document'] for item in sorted_results[:top_k]]

    async def delete_documents(self, filter_dict: Dict[str, Any]) -> int:
        """Delete documents matching filter."""
        result = await self.collection.delete_many(filter_dict)
        logger.info(f"Deleted {result.deleted_count} documents")
        return result.deleted_count

    async def update_document_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> bool:
        """Update document metadata."""
        from bson import ObjectId
        
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(doc_id)},
                {"$set": {"metadata": metadata}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update document metadata: {e}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            stats = await self.db.command("collStats", settings.collection_name)
            count = await self.collection.count_documents({})
            
            return {
                "document_count": count,
                "collection_size": stats.get("size", 0),
                "index_count": stats.get("nindexes", 0),
                "avg_document_size": stats.get("avgObjSize", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

# Global instance
rag_service = MongoDBRAG()

def get_rag_service() -> MongoDBRAG:
    """Dependency injector for the RAG service."""
    return rag_service