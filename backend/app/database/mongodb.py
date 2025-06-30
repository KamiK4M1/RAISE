"""
Prisma database operations - replaces Motor/MongoDB
This module provides Prisma client access and legacy compatibility functions
"""
import logging
from app.core.database import get_prisma_client, connect_database, disconnect_database

logger = logging.getLogger(__name__)

# Legacy compatibility functions for existing code
async def connect_to_mongo():
    """Legacy compatibility - use Prisma instead"""
    await connect_database()

async def close_mongo_connection():
    """Legacy compatibility - use Prisma instead"""
    await disconnect_database()

async def get_database():
    """Legacy compatibility - returns Prisma client"""
    return await get_prisma_client()

def get_collection(collection_name: str):
    """
    Legacy compatibility function - no longer needed with Prisma
    Prisma models are accessed directly via prisma.model_name
    """
    logger.warning(f"get_collection('{collection_name}') is deprecated. Use Prisma models directly.")
    raise NotImplementedError("Use Prisma models directly instead of collections")

# Legacy collection getters - deprecated, use Prisma models instead
async def get_documents_collection():
    logger.warning("get_documents_collection() is deprecated. Use prisma.document instead.")
    raise NotImplementedError("Use prisma.document instead")

async def get_flashcards_collection():
    logger.warning("get_flashcards_collection() is deprecated. Use prisma.flashcard instead.")
    raise NotImplementedError("Use prisma.flashcard instead")

async def get_quizzes_collection():
    logger.warning("get_quizzes_collection() is deprecated. Use prisma.quiz instead.")
    raise NotImplementedError("Use prisma.quiz instead")

async def get_quiz_attempts_collection():
    logger.warning("get_quiz_attempts_collection() is deprecated. Use prisma.quizattempt instead.")
    raise NotImplementedError("Use prisma.quizattempt instead")

async def get_user_progress_collection():
    logger.warning("get_user_progress_collection() is deprecated. Use custom model if needed.")
    raise NotImplementedError("Use custom model if needed")

async def get_chat_history_collection():
    logger.warning("get_chat_history_collection() is deprecated. Use prisma.chatmessage instead.")
    raise NotImplementedError("Use prisma.chatmessage instead")
