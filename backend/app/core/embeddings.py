import asyncio
import aiohttp
from typing import List, Dict, Any
import logging
import numpy as np
from app.config import settings
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        # Use your Hugging Face endpoint URL
        self.embedding_endpoint = getattr(settings, 'embedding_endpoint_url', None)
        if not self.embedding_endpoint:
            raise EmbeddingError("Embedding endpoint URL not configured")
        
        # Optional: Add authentication if your endpoint requires it
        self.auth_token = getattr(settings, 'hf_auth_token', None)

    async def generate_embeddings(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
        """Generate embeddings for a list of texts using Hugging Face endpoint"""
        if not texts:
            return []
        
        for attempt in range(max_retries):
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                
                # Add authentication header if token is provided
                if self.auth_token:
                    headers["Authorization"] = f"Bearer {self.auth_token}"
                
                payload = {
                    "texts": texts
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.embedding_endpoint}/api/embeddings",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(
                            total=900,  # 15 minutes total timeout
                            connect=60,  # 60 seconds to establish connection
                            sock_read=600,  # 10 minutes to read response
                            sock_connect=60  # 60 seconds for socket connection
                        )
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise EmbeddingError(f"Embedding API error: {response.status} - {error_text}")
                        
                        result = await response.json()
                        
                        if not result.get("success"):
                            raise EmbeddingError(f"Embedding API returned error: {result.get('error', 'Unknown error')}")
                        
                        embeddings = result.get("embeddings", [])
                        logger.info(f"Generated embeddings for {len(texts)} texts")
                        return embeddings
            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"HTTP client error after {max_retries} attempts: {e}")
                    raise EmbeddingError(f"Failed to connect to embedding service: {str(e)}")
                
                # Exponential backoff: wait 2^attempt seconds
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                continue
            except Exception as e:
                logger.error(f"Embedding generation error: {e}")
                raise EmbeddingError(f"เกิดข้อผิดพลาดในการสร้าง embedding: {str(e)}")

    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []

    async def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)
            
            # Compute cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity computation error: {e}")
            return 0.0

    async def compute_similarity_texts(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts using the endpoint"""
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            payload = {
                "text1": text1,
                "text2": text2
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.embedding_endpoint}/api/similarity",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(
                        total=120,  # 2 minutes for similarity computation
                        connect=30,  # 30 seconds to establish connection
                        sock_read=90,  # 90 seconds to read response
                        sock_connect=30  # 30 seconds for socket connection
                    )
                ) as response:
                    if response.status != 200:
                        # Fallback to local computation if endpoint doesn't support similarity
                        emb1 = await self.generate_single_embedding(text1)
                        emb2 = await self.generate_single_embedding(text2)
                        return await self.compute_similarity(emb1, emb2)
                    
                    result = await response.json()
                    
                    if result.get("success"):
                        return result.get("similarity", 0.0)
                    else:
                        # Fallback to local computation
                        emb1 = await self.generate_single_embedding(text1)
                        emb2 = await self.generate_single_embedding(text2)
                        return await self.compute_similarity(emb1, emb2)
                        
        except Exception as e:
            logger.error(f"Similarity computation error: {e}")
            # Fallback to local computation
            try:
                emb1 = await self.generate_single_embedding(text1)
                emb2 = await self.generate_single_embedding(text2)
                return await self.compute_similarity(emb1, emb2)
            except:
                return 0.0

    async def find_most_similar(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find most similar embeddings to query"""
        try:
            query_emb = np.array(query_embedding)
            similarities = []
            
            for i, candidate_emb in enumerate(candidate_embeddings):
                candidate_array = np.array(candidate_emb)
                similarity = np.dot(query_emb, candidate_array) / (
                    np.linalg.norm(query_emb) * np.linalg.norm(candidate_array)
                )
                similarities.append({
                    'index': i,
                    'similarity': float(similarity)
                })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Similar search error: {e}")
            return []

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model"""
        # BGE-M3 produces 1024-dimensional embeddings
        return 1024

# Global instance
embedding_service = EmbeddingService()