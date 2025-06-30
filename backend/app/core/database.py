"""
Prisma database client configuration and management
"""
import logging
from contextlib import asynccontextmanager
from prisma import Prisma
from app.config import settings

logger = logging.getLogger(__name__)

# Global Prisma client instance
prisma_client: Prisma = None

async def get_prisma_client() -> Prisma:
    """Get the global Prisma client instance"""
    global prisma_client
    if prisma_client is None:
        prisma_client = Prisma()
        await prisma_client.connect()
        logger.info("Connected to database via Prisma")
    return prisma_client

async def connect_database():
    """Initialize database connection"""
    try:
        global prisma_client
        if prisma_client is None:
            prisma_client = Prisma()
            await prisma_client.connect()
            logger.info("Successfully connected to MongoDB via Prisma")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise e

async def disconnect_database():
    """Close database connection"""
    global prisma_client
    if prisma_client:
        await prisma_client.disconnect()
        prisma_client = None
        logger.info("Disconnected from database")

@asynccontextmanager
async def get_db_transaction():
    """Context manager for database transactions"""
    client = await get_prisma_client()
    async with client.tx() as transaction:
        yield transaction