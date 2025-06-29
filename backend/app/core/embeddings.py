import asyncio
from typing import List, Dict, Any
import logging
from sentence_transformers import SentenceTransformer
import numpy as np
from app.config import settings
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.model_name = settings.embedding_model
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise EmbeddingError(f"ไม่สามารถโหลดโมเดล embedding ได้: {str(e)}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if not texts:
            return []
        
        try:
            # Run embedding generation in thread pool to avoid blocking
            embeddings = await asyncio.to_thread(
                self.model.encode,
                texts,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            
            # Convert numpy arrays to lists
            return [embedding.tolist() for embedding in embeddings]
            
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
        if self.model:
            return self.model.get_sentence_embedding_dimension()
        return 0

# Global instance
embedding_service = EmbeddingService()