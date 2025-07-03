"""
MongoDB collections management and schema definitions
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from app.core.database import db_manager, get_collection

logger = logging.getLogger(__name__)

class Collections:
    """MongoDB collection names"""
    USERS = "User"
    DOCUMENTS = "documents"
    DOCUMENT_CHUNKS = "document_chunks"
    FLASHCARDS = "flashcards"
    QUIZZES = "quizzes"
    QUIZ_ATTEMPTS = "quiz_attempts"
    CHAT_MESSAGES = "chat_messages"

class MongoDBManager:
    """MongoDB collections and schema management"""
    
    def __init__(self):
        self._indexes_created = False
    
    async def initialize_collections(self):
        """Initialize all collections and create indexes"""
        try:
            await self.create_indexes()
            logger.info("MongoDB collections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise
    
    async def create_indexes(self):
        """Create indexes for all collections"""
        if self._indexes_created:
            return
            
        try:
            # Users collection indexes
            users_collection = get_collection(Collections.USERS)
            await users_collection.create_index([("email", ASCENDING)], unique=True)
            await users_collection.create_index([("created_at", DESCENDING)])
            
            # Documents collection indexes
            documents_collection = get_collection(Collections.DOCUMENTS)
            await documents_collection.create_index([("user_id", ASCENDING)])
            await documents_collection.create_index([("status", ASCENDING)])
            await documents_collection.create_index([("created_at", DESCENDING)])
            await documents_collection.create_index([("title", TEXT), ("content", TEXT)])
            
            # Document chunks collection indexes
            chunks_collection = get_collection(Collections.DOCUMENT_CHUNKS)
            await chunks_collection.create_index([("document_id", ASCENDING)])
            await chunks_collection.create_index([("chunk_index", ASCENDING)])
            await chunks_collection.create_index([
                ("document_id", ASCENDING), 
                ("chunk_index", ASCENDING)
            ], unique=True)
            
            # Create vector search index (Atlas only)
            await self.create_vector_search_index(chunks_collection)
            
            # Flashcards collection indexes
            flashcards_collection = get_collection(Collections.FLASHCARDS)
            await flashcards_collection.create_index([("user_id", ASCENDING)])
            await flashcards_collection.create_index([("document_id", ASCENDING)])
            await flashcards_collection.create_index([("next_review", ASCENDING)])
            await flashcards_collection.create_index([
                ("user_id", ASCENDING), 
                ("next_review", ASCENDING)
            ])
            
            # Quizzes collection indexes
            quizzes_collection = get_collection(Collections.QUIZZES)
            await quizzes_collection.create_index([("document_id", ASCENDING)])
            await quizzes_collection.create_index([("created_at", DESCENDING)])
            
            # Quiz attempts collection indexes
            attempts_collection = get_collection(Collections.QUIZ_ATTEMPTS)
            await attempts_collection.create_index([("user_id", ASCENDING)])
            await attempts_collection.create_index([("quiz_id", ASCENDING)])
            await attempts_collection.create_index([("completed_at", DESCENDING)])
            await attempts_collection.create_index([
                ("user_id", ASCENDING), 
                ("quiz_id", ASCENDING)
            ])
            
            # Chat messages collection indexes
            chat_collection = get_collection(Collections.CHAT_MESSAGES)
            await chat_collection.create_index([("user_id", ASCENDING)])
            await chat_collection.create_index([("document_id", ASCENDING)])
            await chat_collection.create_index([("session_id", ASCENDING)])
            await chat_collection.create_index([("created_at", DESCENDING)])
            
            self._indexes_created = True
            logger.info("All MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    async def create_vector_search_index(self, collection: AsyncIOMotorCollection):
        """Create vector search index for embeddings (Atlas only)"""
        try:
            from app.config import settings
            
            # Skip if not configured or not using Atlas
            if not settings.mongodb_vector_search_index:
                logger.info("Vector search index not configured, skipping")
                return
                
            # Check if we're using MongoDB Atlas (contains .mongodb.net)
            if ".mongodb.net" not in settings.mongodb_uri:
                logger.info("Not using MongoDB Atlas, skipping vector search index")
                return
            
            index_name = settings.mongodb_vector_search_index
            
            # Vector search index definition for BGE-M3 (1024 dimensions)
            vector_index_definition = {
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": 1024,
                        "similarity": "cosine"
                    }
                ]
            }
            
            # Try to create the index (this requires Atlas API or MongoDB Compass)
            # Note: Vector search indexes cannot be created via driver, must use Atlas UI/API
            logger.warning(
                f"Vector search index '{index_name}' must be created manually in MongoDB Atlas. "
                f"Use the following definition in Atlas Search: {vector_index_definition}"
            )
            
        except Exception as e:
            logger.warning(f"Could not setup vector search index: {e}")
            # Don't raise - vector search is optional
    
    def get_users_collection(self) -> AsyncIOMotorCollection:
        """Get users collection"""
        return get_collection(Collections.USERS)
    
    def get_documents_collection(self) -> AsyncIOMotorCollection:
        """Get documents collection"""
        return get_collection(Collections.DOCUMENTS)
    
    def get_document_chunks_collection(self) -> AsyncIOMotorCollection:
        """Get document chunks collection"""
        return get_collection(Collections.DOCUMENT_CHUNKS)
    
    def get_flashcards_collection(self) -> AsyncIOMotorCollection:
        """Get flashcards collection"""
        return get_collection(Collections.FLASHCARDS)
    
    def get_quizzes_collection(self) -> AsyncIOMotorCollection:
        """Get quizzes collection"""
        return get_collection(Collections.QUIZZES)
    
    def get_quiz_attempts_collection(self) -> AsyncIOMotorCollection:
        """Get quiz attempts collection"""
        return get_collection(Collections.QUIZ_ATTEMPTS)
    
    def get_chat_messages_collection(self) -> AsyncIOMotorCollection:
        """Get chat messages collection"""
        return get_collection(Collections.CHAT_MESSAGES)

# Document schemas for validation
def create_user_document(
    name: Optional[str],
    email: str,
    password: str,
    role: str = "user"
) -> Dict[str, Any]:
    """Create user document"""
    return {
        "name": name,
        "email": email,
        "password": password,
        "role": role,
        "email_verified": None,
        "image": None,
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }

def create_document_document(
    user_id: str,
    title: str,
    filename: str,
    content: str,
    file_type: str,
    file_size: int,
    upload_path: Optional[str] = None
) -> Dict[str, Any]:
    """Create document document"""
    return {
        "user_id": ObjectId(user_id),
        "title": title,
        "filename": filename,
        "content": content,
        "file_type": file_type,
        "file_size": file_size,
        "upload_path": upload_path,
        "status": "processing",
        "processing_progress": 0,
        "error_message": None,
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }

def create_document_chunk_document(
    document_id: str,
    chunk_index: int,
    text: str,
    embedding: List[float],
    start_pos: Optional[int] = None,
    end_pos: Optional[int] = None
) -> Dict[str, Any]:
    """Create document chunk document"""
    return {
        "document_id": ObjectId(document_id),
        "chunk_index": chunk_index,
        "text": text,
        "embedding": embedding,
        "start_pos": start_pos,
        "end_pos": end_pos,
        "created_at": datetime.datetime.utcnow()
    }

def create_flashcard_document(
    user_id: str,
    document_id: str,
    question: str,
    answer: str,
    difficulty: str = "medium"
) -> Dict[str, Any]:
    """Create flashcard document"""
    return {
        "user_id": ObjectId(user_id),
        "document_id": ObjectId(document_id),
        "question": question,
        "answer": answer,
        "difficulty": difficulty,
        "ease_factor": 2.5,
        "interval": 1,
        "next_review": datetime.datetime.utcnow(),
        "review_count": 0,
        "correct_count": 0,
        "incorrect_count": 0,
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }

def create_quiz_document(
    document_id: str,
    title: str,
    description: Optional[str],
    questions: List[Dict[str, Any]],
    total_points: int,
    time_limit: Optional[int] = None
) -> Dict[str, Any]:
    """Create quiz document"""
    return {
        "document_id": ObjectId(document_id),
        "title": title,
        "description": description,
        "questions": questions,
        "total_points": total_points,
        "time_limit": time_limit,
        "attempts_allowed": -1,  # Unlimited by default
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }

def create_quiz_attempt_document(
    user_id: str,
    quiz_id: str,
    answers: List[str],
    score: float,
    total_points: int,
    percentage: float,
    time_taken: int
) -> Dict[str, Any]:
    """Create quiz attempt document"""
    return {
        "user_id": ObjectId(user_id),
        "quiz_id": ObjectId(quiz_id),
        "answers": answers,
        "score": score,
        "total_points": total_points,
        "percentage": percentage,
        "time_taken": time_taken,
        "completed_at": datetime.datetime.utcnow()
    }

def create_chat_message_document(
    user_id: str,
    document_id: str,
    question: str,
    answer: str,
    session_id: Optional[str] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
    confidence: Optional[float] = None
) -> Dict[str, Any]:
    """Create chat message document"""
    return {
        "user_id": ObjectId(user_id),
        "document_id": ObjectId(document_id),
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "sources": sources or [],
        "confidence": confidence,
        "created_at": datetime.datetime.utcnow()
    }

# Global MongoDB manager instance
mongodb_manager = MongoDBManager()

# Compatibility functions
async def connect_to_mongo():
    """Connect to MongoDB and initialize collections"""
    await db_manager.connect()
    await mongodb_manager.initialize_collections()

async def close_mongo_connection():
    """Close MongoDB connection"""
    await db_manager.disconnect()

async def get_database():
    """Returns motor database client"""
    return db_manager.get_database()