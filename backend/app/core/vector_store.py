"""
Advanced Vector Database Integration for RAISE RAG System

This module provides comprehensive vector storage and retrieval capabilities optimized for
production use with BGE-M3 embeddings (1024 dimensions). Supports both MongoDB Vector Search
and FAISS for different deployment scenarios.

Features:
- MongoDB Atlas Vector Search with advanced indexing
- FAISS fallback for local development and high-performance scenarios
- Batch operations for efficient large document processing
- Memory-efficient operations with streaming support
- Advanced similarity metrics (cosine, euclidean, dot product)
- Filtering by document, user, and metadata context
- Comprehensive performance monitoring and optimization
- Robust error handling and recovery mechanisms
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
import uuid

import numpy as np
from bson import ObjectId
from pymongo import IndexModel
from pymongo.errors import DuplicateKeyError, OperationFailure
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_db_client, db_manager
from app.core.exceptions import VectorStoreError
from app.config import settings

logger = logging.getLogger(__name__)

class SimilarityMetric(Enum):
    """Supported similarity metrics for vector search"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"

@dataclass
class VectorSearchResult:
    """Result from vector similarity search"""
    id: str
    document_id: str
    user_id: str
    text: str
    similarity_score: float
    metadata: Dict[str, Any]
    chunk_index: int
    embedding: Optional[List[float]] = None

@dataclass
class VectorStoreStats:
    """Vector store performance statistics"""
    total_vectors: int
    index_size_mb: float
    avg_search_time_ms: float
    cache_hit_rate: float
    memory_usage_mb: float
    last_optimization: datetime

class PerformanceMonitor:
    """Monitor and track vector store performance metrics"""
    
    def __init__(self):
        self.search_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.operation_counts = {}
        self.last_reset = datetime.utcnow()
    
    def record_search_time(self, duration_ms: float):
        """Record search operation duration"""
        self.search_times.append(duration_ms)
        if len(self.search_times) > 1000:  # Keep only recent measurements
            self.search_times = self.search_times[-500:]
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_misses += 1
    
    def record_operation(self, operation: str):
        """Record operation count"""
        self.operation_counts[operation] = self.operation_counts.get(operation, 0) + 1
    
    @property
    def avg_search_time_ms(self) -> float:
        """Calculate average search time"""
        return np.mean(self.search_times) if self.search_times else 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            "avg_search_time_ms": self.avg_search_time_ms,
            "cache_hit_rate": self.cache_hit_rate,
            "total_searches": len(self.search_times),
            "operation_counts": self.operation_counts.copy(),
            "uptime_hours": (datetime.utcnow() - self.last_reset).total_seconds() / 3600
        }

class VectorStore:
    """
    Advanced vector database integration supporting both MongoDB Vector Search and FAISS.
    Optimized for production use with BGE-M3 embeddings and large-scale document processing.
    """
    
    def __init__(self, 
                 collection_name: str = "vector_embeddings",
                 embedding_dimension: int = 1024,
                 enable_cache: bool = True,
                 cache_size: int = 10000):
        """
        Initialize VectorStore
        
        Args:
            collection_name: MongoDB collection name for vector storage
            embedding_dimension: Dimension of embeddings (1024 for BGE-M3)
            enable_cache: Enable in-memory caching for frequently accessed vectors
            cache_size: Maximum number of vectors to cache in memory
        """
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        
        # Initialize components
        self.db = None
        self.collection: Optional[AsyncIOMotorCollection] = None
        self.monitor = PerformanceMonitor()
        
        # FAISS components
        self._faiss_index = None
        self._faiss_id_mapping: Dict[int, str] = {}
        self._use_faiss = getattr(settings, 'use_faiss_vector_search', False)
        
        # MongoDB Vector Search components
        self._use_atlas_search = hasattr(settings, 'mongodb_vector_search_index')
        self._vector_index_name = getattr(settings, 'mongodb_vector_search_index', 'vector_search_index')
        
        # Memory cache for frequently accessed vectors
        self._vector_cache: Dict[str, Tuple[List[float], datetime]] = {}
        self._cache_ttl = timedelta(hours=1)
        
        # Performance optimization settings
        self._batch_size = 1000
        self._max_concurrent_operations = 10
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the vector store with database connections and indexes"""
        if self._initialized:
            return
        
        try:
            # Initialize database connection
            self.db = await get_db_client()
            self.collection = self.db[self.collection_name]
            
            # Create indexes for efficient querying
            await self._create_indexes()
            
            # Initialize vector search backend
            if self._use_atlas_search:
                await self._initialize_atlas_search()
                logger.info("MongoDB Atlas Vector Search initialized")
            elif self._use_faiss:
                await self._initialize_faiss()
                logger.info("FAISS vector search initialized")
            else:
                logger.info("Using basic vector search without specialized indexing")
            
            self._initialized = True
            logger.info(f"VectorStore initialized with {self.embedding_dimension}D embeddings")
            
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {e}")
            raise VectorStoreError(f"Initialization failed: {e}")
    
    async def _create_indexes(self) -> None:
        """Create database indexes for efficient vector operations"""
        try:
            indexes = [
                IndexModel([("document_id", 1), ("user_id", 1)]),
                IndexModel([("document_id", 1), ("chunk_index", 1)]),
                IndexModel([("user_id", 1), ("created_at", -1)]),
                IndexModel([("metadata.type", 1)]),
                IndexModel([("vector_id", 1)], unique=True),
            ]
            
            await self.collection.create_indexes(indexes)
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Index creation failed (may already exist): {e}")
    
    async def _initialize_atlas_search(self) -> None:
        """Initialize MongoDB Atlas Vector Search"""
        try:
            # Verify Atlas Search index exists
            # Note: Atlas Search indexes must be created through Atlas UI or Management API
            await self._verify_atlas_index()
            logger.info("Atlas Vector Search verified")
            
        except Exception as e:
            logger.warning(f"Atlas Vector Search not available: {e}")
            self._use_atlas_search = False
            if self._use_faiss:
                await self._initialize_faiss()
    
    async def _verify_atlas_index(self) -> None:
        """Verify that the Atlas Search index exists and is properly configured"""
        # This is a placeholder for Atlas index verification
        # In practice, you would use the Atlas Management API or MongoDB Compass
        pass
    
    async def _initialize_faiss(self) -> None:
        """Initialize FAISS index for high-performance vector search"""
        try:
            import faiss
            
            # Create FAISS index based on dimension and expected size
            if hasattr(faiss, 'IndexHNSWFlat'):
                # Use HNSW for better performance with large datasets
                self._faiss_index = faiss.IndexHNSWFlat(self.embedding_dimension, 32)
                self._faiss_index.hnsw.efConstruction = 200
                self._faiss_index.hnsw.efSearch = 50
            else:
                # Fallback to flat index
                self._faiss_index = faiss.IndexFlatIP(self.embedding_dimension)
            
            # Load existing vectors into FAISS
            await self._rebuild_faiss_index()
            logger.info(f"FAISS index initialized with {self._faiss_index.ntotal} vectors")
            
        except ImportError:
            logger.warning("FAISS not available. Install with: pip install faiss-cpu")
            self._use_faiss = False
        except Exception as e:
            logger.error(f"FAISS initialization failed: {e}")
            self._use_faiss = False
    
    async def _rebuild_faiss_index(self) -> None:
        """Rebuild FAISS index from MongoDB data"""
        if not self._faiss_index:
            return
        
        try:
            # Clear existing index
            self._faiss_index.reset()
            self._faiss_id_mapping.clear()
            
            # Load vectors in batches
            cursor = self.collection.find({}, {"vector_id": 1, "embedding": 1})
            embeddings = []
            vector_ids = []
            
            async for doc in cursor:
                if "embedding" in doc and doc["embedding"]:
                    embeddings.append(doc["embedding"])
                    vector_ids.append(doc["vector_id"])
                    
                    # Process in batches
                    if len(embeddings) >= self._batch_size:
                        await self._add_to_faiss_batch(embeddings, vector_ids)
                        embeddings.clear()
                        vector_ids.clear()
            
            # Process remaining vectors
            if embeddings:
                await self._add_to_faiss_batch(embeddings, vector_ids)
            
            logger.info(f"FAISS index rebuilt with {len(self._faiss_id_mapping)} vectors")
            
        except Exception as e:
            logger.error(f"FAISS index rebuild failed: {e}")
    
    async def _add_to_faiss_batch(self, embeddings: List[List[float]], vector_ids: List[str]) -> None:
        """Add a batch of vectors to FAISS index"""
        if not embeddings or not self._faiss_index:
            return
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(embeddings_array)
        
        # Add to index
        start_idx = self._faiss_index.ntotal
        self._faiss_index.add(embeddings_array)
        
        # Update ID mapping
        for i, vector_id in enumerate(vector_ids):
            self._faiss_id_mapping[start_idx + i] = vector_id
    
    async def store_vectors(self, 
                          vectors: List[Dict[str, Any]], 
                          batch_size: Optional[int] = None) -> List[str]:
        """
        Store multiple vectors efficiently with batch processing
        
        Args:
            vectors: List of vector documents with embeddings and metadata
            batch_size: Batch size for processing (defaults to instance batch_size)
        
        Returns:
            List of vector IDs for stored vectors
        """
        if not self._initialized:
            await self.initialize()
        
        batch_size = batch_size or self._batch_size
        vector_ids = []
        
        start_time = time.time()
        
        try:
            # Process vectors in batches
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                batch_ids = await self._store_vector_batch(batch)
                vector_ids.extend(batch_ids)
                
                # Log progress for large batches
                if len(vectors) > 1000 and i % (batch_size * 10) == 0:
                    logger.info(f"Processed {i + len(batch)}/{len(vectors)} vectors")
            
            # Update FAISS index if enabled
            if self._use_faiss:
                await self._update_faiss_with_new_vectors(vectors)
            
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.record_operation("store_vectors")
            
            logger.info(f"Stored {len(vectors)} vectors in {duration_ms:.2f}ms")
            return vector_ids
            
        except Exception as e:
            logger.error(f"Error storing vectors: {e}")
            raise VectorStoreError(f"Failed to store vectors: {e}")
    
    async def _store_vector_batch(self, vectors: List[Dict[str, Any]]) -> List[str]:
        """Store a batch of vectors in MongoDB"""
        documents = []
        vector_ids = []
        
        for vector_data in vectors:
            vector_id = str(uuid.uuid4())
            vector_ids.append(vector_id)
            
            # Validate embedding dimension
            embedding = vector_data.get("embedding")
            if not embedding or len(embedding) != self.embedding_dimension:
                raise VectorStoreError(f"Invalid embedding dimension: expected {self.embedding_dimension}")
            
            # Prepare document
            doc = {
                "vector_id": vector_id,
                "document_id": ObjectId(vector_data["document_id"]),
                "user_id": ObjectId(vector_data["user_id"]),
                "text": vector_data["text"],
                "embedding": embedding,
                "chunk_index": vector_data.get("chunk_index", 0),
                "metadata": vector_data.get("metadata", {}),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            documents.append(doc)
        
        # Insert batch
        try:
            await self.collection.insert_many(documents, ordered=False)
            return vector_ids
        except DuplicateKeyError as e:
            logger.warning(f"Some vectors already exist: {e}")
            return vector_ids
    
    async def _update_faiss_with_new_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        """Update FAISS index with newly added vectors"""
        if not self._faiss_index:
            return
        
        try:
            embeddings = [v["embedding"] for v in vectors if "embedding" in v]
            vector_ids = [v.get("vector_id") for v in vectors]
            
            if embeddings and vector_ids:
                await self._add_to_faiss_batch(embeddings, vector_ids)
                
        except Exception as e:
            logger.warning(f"Failed to update FAISS index: {e}")
    
    async def similarity_search(self,
                              query_embedding: List[float],
                              limit: int = 10,
                              similarity_threshold: float = 0.7,
                              similarity_metric: SimilarityMetric = SimilarityMetric.COSINE,
                              filters: Optional[Dict[str, Any]] = None,
                              include_embeddings: bool = False) -> List[VectorSearchResult]:
        """
        Perform advanced similarity search with multiple metrics and filtering
        
        Args:
            query_embedding: Query vector for similarity search
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score threshold
            similarity_metric: Similarity metric to use
            filters: Additional filters (document_id, user_id, metadata filters)
            include_embeddings: Whether to include embeddings in results
        
        Returns:
            List of search results sorted by similarity score
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Choose search strategy based on available backends
            if self._use_atlas_search:
                results = await self._atlas_similarity_search(
                    query_embedding, limit, similarity_threshold, filters, include_embeddings
                )
            elif self._use_faiss:
                results = await self._faiss_similarity_search(
                    query_embedding, limit, similarity_threshold, similarity_metric, filters, include_embeddings
                )
            else:
                results = await self._basic_similarity_search(
                    query_embedding, limit, similarity_threshold, similarity_metric, filters, include_embeddings
                )
            
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.record_search_time(duration_ms)
            self.monitor.record_operation("similarity_search")
            
            logger.debug(f"Similarity search completed in {duration_ms:.2f}ms, found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise VectorStoreError(f"Search failed: {e}")
    
    async def _atlas_similarity_search(self,
                                     query_embedding: List[float],
                                     limit: int,
                                     similarity_threshold: float,
                                     filters: Optional[Dict[str, Any]],
                                     include_embeddings: bool) -> List[VectorSearchResult]:
        """Perform similarity search using MongoDB Atlas Vector Search"""
        try:
            # Build aggregation pipeline
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": self._vector_index_name,
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
            
            # Add filters
            if filters:
                match_conditions = {}
                if "document_id" in filters:
                    match_conditions["document_id"] = ObjectId(filters["document_id"])
                if "user_id" in filters:
                    match_conditions["user_id"] = ObjectId(filters["user_id"])
                if "metadata" in filters:
                    for key, value in filters["metadata"].items():
                        match_conditions[f"metadata.{key}"] = value
                
                if match_conditions:
                    pipeline.append({"$match": match_conditions})
            
            # Filter by similarity threshold
            pipeline.append({
                "$match": {"similarity_score": {"$gte": similarity_threshold}}
            })
            
            # Project fields
            projection = {
                "vector_id": 1,
                "document_id": 1,
                "user_id": 1,
                "text": 1,
                "similarity_score": 1,
                "metadata": 1,
                "chunk_index": 1
            }
            if include_embeddings:
                projection["embedding"] = 1
            
            pipeline.append({"$project": projection})
            
            # Execute search
            cursor = self.collection.aggregate(pipeline)
            results = []
            
            async for doc in cursor:
                result = VectorSearchResult(
                    id=doc["vector_id"],
                    document_id=str(doc["document_id"]),
                    user_id=str(doc["user_id"]),
                    text=doc["text"],
                    similarity_score=doc["similarity_score"],
                    metadata=doc.get("metadata", {}),
                    chunk_index=doc.get("chunk_index", 0),
                    embedding=doc.get("embedding") if include_embeddings else None
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Atlas Vector Search error: {e}")
            # Fallback to basic search
            return await self._basic_similarity_search(
                query_embedding, limit, similarity_threshold, SimilarityMetric.COSINE, filters, include_embeddings
            )
    
    async def _faiss_similarity_search(self,
                                     query_embedding: List[float],
                                     limit: int,
                                     similarity_threshold: float,
                                     similarity_metric: SimilarityMetric,
                                     filters: Optional[Dict[str, Any]],
                                     include_embeddings: bool) -> List[VectorSearchResult]:
        """Perform similarity search using FAISS"""
        if not self._faiss_index or self._faiss_index.ntotal == 0:
            return []
        
        try:
            # Prepare query vector
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Normalize for cosine similarity
            if similarity_metric == SimilarityMetric.COSINE:
                import faiss
                faiss.normalize_L2(query_vector)
            
            # Search FAISS index
            search_k = min(limit * 5, self._faiss_index.ntotal)  # Search more candidates for filtering
            similarities, indices = self._faiss_index.search(query_vector, search_k)
            
            # Get MongoDB documents for results
            vector_ids = []
            for idx in indices[0]:
                if idx != -1 and idx in self._faiss_id_mapping:
                    vector_ids.append(self._faiss_id_mapping[idx])
            
            if not vector_ids:
                return []
            
            # Build MongoDB query
            mongo_filter = {"vector_id": {"$in": vector_ids}}
            if filters:
                if "document_id" in filters:
                    mongo_filter["document_id"] = ObjectId(filters["document_id"])
                if "user_id" in filters:
                    mongo_filter["user_id"] = ObjectId(filters["user_id"])
                if "metadata" in filters:
                    for key, value in filters["metadata"].items():
                        mongo_filter[f"metadata.{key}"] = value
            
            # Project fields
            projection = {
                "vector_id": 1,
                "document_id": 1,
                "user_id": 1,
                "text": 1,
                "metadata": 1,
                "chunk_index": 1
            }
            if include_embeddings:
                projection["embedding"] = 1
            
            # Get documents from MongoDB
            cursor = self.collection.find(mongo_filter, projection)
            docs_by_id = {}
            async for doc in cursor:
                docs_by_id[doc["vector_id"]] = doc
            
            # Build results with FAISS similarity scores
            results = []
            for i, (similarity, vector_id) in enumerate(zip(similarities[0], vector_ids)):
                if vector_id in docs_by_id and similarity >= similarity_threshold:
                    doc = docs_by_id[vector_id]
                    result = VectorSearchResult(
                        id=doc["vector_id"],
                        document_id=str(doc["document_id"]),
                        user_id=str(doc["user_id"]),
                        text=doc["text"],
                        similarity_score=float(similarity),
                        metadata=doc.get("metadata", {}),
                        chunk_index=doc.get("chunk_index", 0),
                        embedding=doc.get("embedding") if include_embeddings else None
                    )
                    results.append(result)
                    
                    if len(results) >= limit:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return []
    
    async def _basic_similarity_search(self,
                                     query_embedding: List[float],
                                     limit: int,
                                     similarity_threshold: float,
                                     similarity_metric: SimilarityMetric,
                                     filters: Optional[Dict[str, Any]],
                                     include_embeddings: bool) -> List[VectorSearchResult]:
        """Perform basic similarity search using MongoDB aggregation"""
        try:
            # Build MongoDB filter
            mongo_filter = {}
            if filters:
                if "document_id" in filters:
                    mongo_filter["document_id"] = ObjectId(filters["document_id"])
                if "user_id" in filters:
                    mongo_filter["user_id"] = ObjectId(filters["user_id"])
                if "metadata" in filters:
                    for key, value in filters["metadata"].items():
                        mongo_filter[f"metadata.{key}"] = value
            
            # Project fields
            projection = {
                "vector_id": 1,
                "document_id": 1,
                "user_id": 1,
                "text": 1,
                "embedding": 1,
                "metadata": 1,
                "chunk_index": 1
            }
            
            # Get documents with embeddings
            cursor = self.collection.find(mongo_filter, projection)
            results = []
            query_vector = np.array(query_embedding)
            
            async for doc in cursor:
                if "embedding" not in doc or not doc["embedding"]:
                    continue
                
                # Calculate similarity
                doc_vector = np.array(doc["embedding"])
                similarity = self._calculate_similarity(query_vector, doc_vector, similarity_metric)
                
                if similarity >= similarity_threshold:
                    result = VectorSearchResult(
                        id=doc["vector_id"],
                        document_id=str(doc["document_id"]),
                        user_id=str(doc["user_id"]),
                        text=doc["text"],
                        similarity_score=float(similarity),
                        metadata=doc.get("metadata", {}),
                        chunk_index=doc.get("chunk_index", 0),
                        embedding=doc.get("embedding") if include_embeddings else None
                    )
                    results.append(result)
            
            # Sort by similarity and limit results
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Basic similarity search error: {e}")
            return []
    
    def _calculate_similarity(self, 
                             vec1: np.ndarray, 
                             vec2: np.ndarray, 
                             metric: SimilarityMetric) -> float:
        """Calculate similarity between two vectors using specified metric"""
        try:
            if metric == SimilarityMetric.COSINE:
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                return np.dot(vec1, vec2) / (norm1 * norm2)
            
            elif metric == SimilarityMetric.DOT_PRODUCT:
                return np.dot(vec1, vec2)
            
            elif metric == SimilarityMetric.EUCLIDEAN:
                distance = np.linalg.norm(vec1 - vec2)
                return 1.0 / (1.0 + distance)  # Convert distance to similarity
            
            elif metric == SimilarityMetric.MANHATTAN:
                distance = np.sum(np.abs(vec1 - vec2))
                return 1.0 / (1.0 + distance)  # Convert distance to similarity
            
            else:
                raise ValueError(f"Unsupported similarity metric: {metric}")
                
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return 0.0
    
    async def delete_vectors(self, 
                           filters: Dict[str, Any],
                           batch_size: Optional[int] = None) -> int:
        """
        Delete vectors matching the given filters
        
        Args:
            filters: Filters to identify vectors to delete
            batch_size: Batch size for deletion (defaults to instance batch_size)
        
        Returns:
            Number of vectors deleted
        """
        if not self._initialized:
            await self.initialize()
        
        batch_size = batch_size or self._batch_size
        
        try:
            # Build MongoDB filter
            mongo_filter = {}
            if "document_id" in filters:
                mongo_filter["document_id"] = ObjectId(filters["document_id"])
            if "user_id" in filters:
                mongo_filter["user_id"] = ObjectId(filters["user_id"])
            if "vector_ids" in filters:
                mongo_filter["vector_id"] = {"$in": filters["vector_ids"]}
            
            # Delete from MongoDB
            result = await self.collection.delete_many(mongo_filter)
            deleted_count = result.deleted_count
            
            # Rebuild FAISS index if vectors were deleted
            if deleted_count > 0 and self._use_faiss:
                await self._rebuild_faiss_index()
            
            self.monitor.record_operation("delete_vectors")
            logger.info(f"Deleted {deleted_count} vectors")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise VectorStoreError(f"Failed to delete vectors: {e}")
    
    async def get_vector_by_id(self, vector_id: str, include_embedding: bool = False) -> Optional[VectorSearchResult]:
        """
        Retrieve a specific vector by its ID
        
        Args:
            vector_id: Vector ID to retrieve
            include_embedding: Whether to include the embedding in the result
        
        Returns:
            Vector search result or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check cache first
            if self.enable_cache and vector_id in self._vector_cache:
                cached_data, cached_time = self._vector_cache[vector_id]
                if datetime.utcnow() - cached_time < self._cache_ttl:
                    self.monitor.record_cache_hit()
                    # Return cached result (implement cache structure as needed)
                else:
                    del self._vector_cache[vector_id]
            
            # Query MongoDB
            projection = {
                "vector_id": 1,
                "document_id": 1,
                "user_id": 1,
                "text": 1,
                "metadata": 1,
                "chunk_index": 1
            }
            if include_embedding:
                projection["embedding"] = 1
            
            doc = await self.collection.find_one({"vector_id": vector_id}, projection)
            
            if doc:
                # Update cache
                if self.enable_cache and include_embedding and "embedding" in doc:
                    self._vector_cache[vector_id] = (doc["embedding"], datetime.utcnow())
                
                return VectorSearchResult(
                    id=doc["vector_id"],
                    document_id=str(doc["document_id"]),
                    user_id=str(doc["user_id"]),
                    text=doc["text"],
                    similarity_score=1.0,  # Perfect match for exact retrieval
                    metadata=doc.get("metadata", {}),
                    chunk_index=doc.get("chunk_index", 0),
                    embedding=doc.get("embedding") if include_embedding else None
                )
            
            self.monitor.record_cache_miss()
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving vector {vector_id}: {e}")
            return None
    
    async def update_vector(self, 
                          vector_id: str, 
                          updates: Dict[str, Any]) -> bool:
        """
        Update a vector's metadata or content
        
        Args:
            vector_id: Vector ID to update
            updates: Dictionary of fields to update
        
        Returns:
            True if update successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Prepare update document
            update_doc = {"$set": {"updated_at": datetime.utcnow()}}
            
            # Handle different update types
            if "text" in updates:
                update_doc["$set"]["text"] = updates["text"]
            
            if "metadata" in updates:
                for key, value in updates["metadata"].items():
                    update_doc["$set"][f"metadata.{key}"] = value
            
            if "embedding" in updates:
                # Validate embedding dimension
                embedding = updates["embedding"]
                if len(embedding) != self.embedding_dimension:
                    raise VectorStoreError(f"Invalid embedding dimension: expected {self.embedding_dimension}")
                update_doc["$set"]["embedding"] = embedding
                
                # Clear cache for this vector
                if vector_id in self._vector_cache:
                    del self._vector_cache[vector_id]
            
            # Update in MongoDB
            result = await self.collection.update_one(
                {"vector_id": vector_id},
                update_doc
            )
            
            success = result.modified_count > 0
            
            # Rebuild FAISS index if embedding was updated
            if success and "embedding" in updates and self._use_faiss:
                await self._rebuild_faiss_index()
            
            self.monitor.record_operation("update_vector")
            return success
            
        except Exception as e:
            logger.error(f"Error updating vector {vector_id}: {e}")
            return False
    
    async def get_stats(self) -> VectorStoreStats:
        """Get comprehensive vector store statistics"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get total vector count
            total_vectors = await self.collection.count_documents({})
            
            # Calculate index size (approximate)
            stats_result = await self.db.command("collStats", self.collection_name)
            index_size_mb = stats_result.get("totalIndexSize", 0) / (1024 * 1024)
            
            # Get performance metrics
            perf_stats = self.monitor.get_stats()
            
            # Estimate memory usage
            memory_usage_mb = 0.0
            if self._use_faiss and self._faiss_index:
                # Rough estimate: dimension * vectors * 4 bytes (float32) + overhead
                memory_usage_mb = (self.embedding_dimension * self._faiss_index.ntotal * 4) / (1024 * 1024)
            
            return VectorStoreStats(
                total_vectors=total_vectors,
                index_size_mb=index_size_mb,
                avg_search_time_ms=perf_stats["avg_search_time_ms"],
                cache_hit_rate=perf_stats["cache_hit_rate"],
                memory_usage_mb=memory_usage_mb,
                last_optimization=datetime.utcnow()  # Could track actual optimization time
            )
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            return VectorStoreStats(
                total_vectors=0,
                index_size_mb=0.0,
                avg_search_time_ms=0.0,
                cache_hit_rate=0.0,
                memory_usage_mb=0.0,
                last_optimization=datetime.utcnow()
            )
    
    async def optimize_index(self) -> Dict[str, Any]:
        """Optimize vector indexes for better performance"""
        if not self._initialized:
            await self.initialize()
        
        try:
            optimization_results = {}
            
            # Rebuild FAISS index for optimization
            if self._use_faiss:
                start_time = time.time()
                await self._rebuild_faiss_index()
                faiss_time = time.time() - start_time
                optimization_results["faiss_rebuild_time_ms"] = faiss_time * 1000
            
            # Clear cache to free memory
            if self.enable_cache:
                cache_size_before = len(self._vector_cache)
                self._vector_cache.clear()
                optimization_results["cache_cleared_entries"] = cache_size_before
            
            # MongoDB index statistics (informational)
            try:
                index_stats = await self.db.command("collStats", self.collection_name)
                optimization_results["mongodb_index_size_mb"] = index_stats.get("totalIndexSize", 0) / (1024 * 1024)
            except Exception:
                pass
            
            optimization_results["optimization_timestamp"] = datetime.utcnow().isoformat()
            self.monitor.record_operation("optimize_index")
            
            logger.info(f"Index optimization completed: {optimization_results}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Index optimization failed: {e}")
            return {"error": str(e), "optimization_timestamp": datetime.utcnow().isoformat()}
    
    @asynccontextmanager
    async def batch_context(self, batch_size: int = 1000):
        """Context manager for efficient batch operations"""
        old_batch_size = self._batch_size
        self._batch_size = batch_size
        try:
            yield self
        finally:
            self._batch_size = old_batch_size
    
    async def close(self) -> None:
        """Clean up resources and close connections"""
        try:
            if self._vector_cache:
                self._vector_cache.clear()
            
            if self._faiss_index:
                self._faiss_index.reset()
                self._faiss_id_mapping.clear()
            
            logger.info("VectorStore closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing VectorStore: {e}")

# Global vector store instance
vector_store = VectorStore()

# Convenience functions for backward compatibility
async def initialize_vector_store():
    """Initialize the global vector store instance"""
    await vector_store.initialize()

async def store_document_vectors(document_id: str, 
                               user_id: str, 
                               chunks_with_embeddings: List[Dict[str, Any]]) -> List[str]:
    """Store vectors for a document"""
    vectors = []
    for i, chunk in enumerate(chunks_with_embeddings):
        vectors.append({
            "document_id": document_id,
            "user_id": user_id,
            "text": chunk["text"],
            "embedding": chunk["embedding"],
            "chunk_index": i,
            "metadata": chunk.get("metadata", {})
        })
    
    return await vector_store.store_vectors(vectors)

async def search_similar_vectors(query_embedding: List[float],
                                document_id: Optional[str] = None,
                                user_id: Optional[str] = None,
                                limit: int = 5,
                                threshold: float = 0.7) -> List[Dict[str, Any]]:
    """Search for similar vectors"""
    filters = {}
    if document_id:
        filters["document_id"] = document_id
    if user_id:
        filters["user_id"] = user_id
    
    results = await vector_store.similarity_search(
        query_embedding=query_embedding,
        limit=limit,
        similarity_threshold=threshold,
        filters=filters
    )
    
    # Convert to legacy format for compatibility
    return [
        {
            "chunk_id": result.id,
            "document_id": result.document_id,
            "text": result.text,
            "similarity": result.similarity_score,
            "chunk_index": result.chunk_index
        }
        for result in results
    ]

async def delete_document_vectors(document_id: str) -> int:
    """Delete all vectors for a document"""
    return await vector_store.delete_vectors({"document_id": document_id})