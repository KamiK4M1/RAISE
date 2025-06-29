from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database():
    return db.database

async def connect_to_mongo():
    try:
        db.client = AsyncIOMotorClient(settings.mongodb_uri)
        db.database = db.client[settings.database_name]
        
        # Test connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes
        await create_indexes()
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create necessary indexes for better performance"""
    try:
        # Documents collection indexes
        await db.database.documents.create_index("user_id")
        await db.database.documents.create_index("document_id")
        
        # Flashcards collection indexes
        await db.database.flashcards.create_index("document_id")
        await db.database.flashcards.create_index("next_review")
        await db.database.flashcards.create_index([("document_id", 1), ("next_review", 1)])
        
        # Quiz attempts collection indexes
        await db.database.quiz_attempts.create_index("user_id")
        await db.database.quiz_attempts.create_index("quiz_id")
        
        # User progress collection indexes
        await db.database.user_progress.create_index([("user_id", 1), ("document_id", 1)])
        
        # Chat history collection indexes
        await db.database.chat_history.create_index("user_id")
        await db.database.chat_history.create_index("created_at")
        
        # Vector search index for document chunks (Atlas Vector Search)
        # This needs to be created through Atlas UI or MongoDB Compass
        logger.info("Indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

# Collection getters
async def get_documents_collection():
    return db.database.documents

async def get_flashcards_collection():
    return db.database.flashcards

async def get_quizzes_collection():
    return db.database.quizzes

async def get_quiz_attempts_collection():
    return db.database.quiz_attempts

async def get_user_progress_collection():
    return db.database.user_progress

async def get_chat_history_collection():
    return db.database.chat_history