"""
Vector Search Implementation for RAISE Learning Platform

This module provides vector similarity search capabilities using:
- MongoDB Atlas Vector Search (for production)
- In-memory FAISS (for local development)
- Document chunk embeddings and retrieval
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from bson import ObjectId

from app.database.mongodb import mongodb_manager
from app.config import settings

logger = logging.getLogger(__name__)

class VectorSearchManager:
    """Manages vector search operations"""
    
    def __init__(self):
        # Initialize attributes to None. They will be populated after the DB connection is up.
        self.chunks_collection = None
        self.use_atlas_search = hasattr(settings, 'mongodb_vector_search_index')
        self.vector_index_name = getattr(settings, 'mongodb_vector_search_index', 'vector_index')
        
        # FAISS fallback for local development
        self._faiss_index = None
        self._faiss_ids = []
        self._use_faiss = getattr(settings, 'use_faiss_vector_search', False)
    
    async def initialize_vector_search(self):
        """Initialize vector search system after the database connection is established."""
        # Now it's safe to get the collection, as this is called from the lifespan startup.
        self.chunks_collection = mongodb_manager.get_document_chunks_collection()
        
        try:
            if self.use_atlas_search:
                await self._initialize_atlas_search()
                logger.info("MongoDB Atlas Vector Search initialized")
            elif self._use_faiss:
                await self._initialize_faiss()
                logger.info("FAISS vector search initialized")
            else:
                logger.info("Using basic similarity search without specialized vector index")
        except Exception as e:
            logger.error(f"Failed to initialize vector search: {e}")
            raise
    
    async def _initialize_atlas_search(self):
        """Initialize MongoDB Atlas Vector Search index"""
        # Note: Atlas Search indexes need to be created through Atlas UI or API
        # This method just verifies the index exists
        try:
            # Check if vector search is available (requires Atlas)
            # This is a placeholder - actual Atlas search setup requires Atlas UI
            pass
        except Exception as e:
            logger.warning(f"Atlas Vector Search not available: {e}")
            self.use_atlas_search = False
    
    async def _initialize_faiss(self):
        """Initialize FAISS index for local development"""
        try:
            import faiss
            
            # Load all embeddings into FAISS
            cursor = self.chunks_collection.find({}, {"embedding": 1, "_id": 1})
            embeddings = []
            ids = []
            
            async for chunk in cursor:
                if "embedding" in chunk and chunk["embedding"]:
                    embeddings.append(chunk["embedding"])
                    ids.append(str(chunk["_id"]))
            
            if embeddings:
                embeddings_array = np.array(embeddings, dtype=np.float32)
                dimension = embeddings_array.shape[1]
                
                # Create FAISS index
                self._faiss_index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
                self._faiss_index.add(embeddings_array)
                self._faiss_ids = ids
                
                logger.info(f"FAISS index created with {len(embeddings)} vectors")
            
        except ImportError:
            logger.warning("FAISS not available. Install with: pip install faiss-cpu")
            self._use_faiss = False
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {e}")
            self._use_faiss = False
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        document_id: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search on document chunks
        
        Args:
            query_embedding: Query vector embedding
            document_id: Optional document ID to filter results
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar chunks with similarity scores
        """
        try:
            if self.use_atlas_search:
                return await self._atlas_similarity_search(
                    query_embedding, document_id, limit, min_similarity
                )
            elif self._use_faiss and self._faiss_index:
                return await self._faiss_similarity_search(
                    query_embedding, document_id, limit, min_similarity
                )
            else:
                return await self._basic_similarity_search(
                    query_embedding, document_id, limit, min_similarity
                )
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    async def _atlas_similarity_search(
        self,
        query_embedding: List[float],
        document_id: Optional[str],
        limit: int,
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """Perform similarity search using MongoDB Atlas Vector Search"""
        try:
            # Atlas Vector Search aggregation pipeline
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": self.vector_index_name,
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": limit * 10,
                        "limit": limit
                    }
                },
                {
                    "$addFields": {
                        "similarity_score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            # Add document filter if specified
            if document_id:
                pipeline.append({
                    "$match": {"document_id": ObjectId(document_id)}
                })
            
            # Filter by minimum similarity
            pipeline.append({
                "$match": {"similarity_score": {"$gte": min_similarity}}
            })
            
            # Execute aggregation
            cursor = self.chunks_collection.aggregate(pipeline)
            results = []
            
            async for chunk in cursor:
                chunk_result = {
                    "chunk_id": str(chunk["_id"]),
                    "document_id": str(chunk["document_id"]),
                    "text": chunk["text"],
                    "similarity": chunk["similarity_score"],
                    "chunk_index": chunk["chunk_index"]
                }
                results.append(chunk_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Atlas Vector Search error: {e}")
            # Fallback to basic search
            return await self._basic_similarity_search(
                query_embedding, document_id, limit, min_similarity
            )
    
    async def _faiss_similarity_search(
        self,
        query_embedding: List[float],
        document_id: Optional[str],
        limit: int,
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """Perform similarity search using FAISS"""
        try:
            if not self._faiss_index:
                return []
            
            # Normalize query vector for cosine similarity
            query_vector = np.array([query_embedding], dtype=np.float32)
            query_vector = query_vector / np.linalg.norm(query_vector)
            
            # Search FAISS index
            similarities, indices = self._faiss_index.search(query_vector, limit * 2)
            
            results = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if similarity < min_similarity:
                    continue
                
                chunk_id = self._faiss_ids[idx]
                
                # Get full chunk data
                chunk = await self.chunks_collection.find_one({"_id": ObjectId(chunk_id)})
                if chunk:
                    # Apply document filter if specified
                    if document_id and str(chunk["document_id"]) != document_id:
                        continue
                    
                    chunk_result = {
                        "chunk_id": str(chunk["_id"]),
                        "document_id": str(chunk["document_id"]),
                        "text": chunk["text"],
                        "similarity": float(similarity),
                        "chunk_index": chunk["chunk_index"]
                    }
                    results.append(chunk_result)
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return []
    
    async def _basic_similarity_search(
        self,
        query_embedding: List[float],
        document_id: Optional[str],
        limit: int,
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """Basic similarity search using dot product"""
        try:
            # Build query filter
            filter_query = {}
            if document_id:
                filter_query["document_id"] = ObjectId(document_id)
            
            # Get all chunks with embeddings
            cursor = self.chunks_collection.find(filter_query)
            results = []
            
            query_vector = np.array(query_embedding)
            query_norm = np.linalg.norm(query_vector)
            
            async for chunk in cursor:
                if "embedding" not in chunk or not chunk["embedding"]:
                    continue
                
                # Calculate cosine similarity
                chunk_vector = np.array(chunk["embedding"])
                chunk_norm = np.linalg.norm(chunk_vector)
                
                if chunk_norm == 0 or query_norm == 0:
                    continue
                
                similarity = np.dot(query_vector, chunk_vector) / (query_norm * chunk_norm)
                
                if similarity >= min_similarity:
                    chunk_result = {
                        "chunk_id": str(chunk["_id"]),
                        "document_id": str(chunk["document_id"]),
                        "text": chunk["text"],
                        "similarity": float(similarity),
                        "chunk_index": chunk["chunk_index"]
                    }
                    results.append(chunk_result)
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Basic similarity search error: {e}")
            return []
    
    async def add_document_embeddings(self, document_id: str, chunks_with_embeddings: List[Dict[str, Any]]):
        """Add embeddings for a document (updates FAISS index if used)"""
        try:
            if self._use_faiss and self._faiss_index:
                # Rebuild FAISS index with new embeddings
                await self._initialize_faiss()
                
        except Exception as e:
            logger.error(f"Error updating vector index: {e}")
    
    async def remove_document_embeddings(self, document_id: str):
        """Remove embeddings for a document"""
        try:
            if self._use_faiss:
                # FAISS doesn't support deletion easily, so rebuild index
                await self._initialize_faiss()
                
        except Exception as e:
            logger.error(f"Error removing from vector index: {e}")

# Global vector search manager
vector_search_manager = VectorSearchManager()

# Convenience functions
async def initialize_vector_search():
    """Initialize vector search system"""
    await vector_search_manager.initialize_vector_search()

async def similarity_search(
    query_embedding: List[float],
    document_id: Optional[str] = None,
    limit: int = 5,
    min_similarity: float = 0.7
) -> List[Dict[str, Any]]:
    """Perform similarity search"""
    return await vector_search_manager.similarity_search(
        query_embedding, document_id, limit, min_similarity
    )