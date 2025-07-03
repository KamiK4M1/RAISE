"""
MongoDB database client configuration and management using motor
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """MongoDB database manager with connection pooling and health checks"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False
    
    async def connect(self):
        """Initialize database connection with proper configuration"""
        try:
            if not self.client:
                # Configure connection with pooling and timeouts
                self.client = AsyncIOMotorClient(
                    settings.mongodb_uri,
                    maxPoolSize=50,
                    minPoolSize=5,
                    maxIdleTimeMS=45000,       
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=20000,
                )
                
                self.db = self.client[settings.database_name]
                
                # Test connection
                await self.client.admin.command('ping')
                self._is_connected = True
                
                logger.info(f"Successfully connected to MongoDB: {settings.database_name}")
                
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._is_connected = False
            raise e
        except Exception as e:
            logger.error(f"Unexpected error connecting to database: {e}")
            self._is_connected = False
            raise e
    
    async def disconnect(self):
        """Close database connection gracefully"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self._is_connected = False
            logger.info("Disconnected from MongoDB")
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            if not self.client:
                return False
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        # ✨ FIX: Check for the database object by comparing it to None
        if not self._is_connected or self.db is None:
            raise ConnectionError("Database not connected. Call connect() first.")
        return self.db
    
    def get_collection(self, collection_name: str):
        """Get collection from database"""
        db = self.get_database()
        return db[collection_name]
    
    @asynccontextmanager
    async def get_transaction(self):
        """Context manager for database transactions"""
        if not self.client:
            raise ConnectionError("Database not connected")
        
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                yield session

# Global database manager instance
db_manager = DatabaseManager()

# Compatibility functions for existing code
async def connect_database():
    """Initialize database connection"""
    await db_manager.connect()

async def disconnect_database():
    """Close database connection"""
    await db_manager.disconnect()

async def get_db_client() -> AsyncIOMotorDatabase:
    """Get the database client instance"""
    if not db_manager._is_connected:
        await db_manager.connect()
    return db_manager.get_database()

def get_collection(collection_name: str):
    """Get collection from database"""
    return db_manager.get_collection(collection_name)

@asynccontextmanager
async def get_db_transaction():
    """Context manager for database transactions"""
    async with db_manager.get_transaction() as session:
        yield session

async def database_health_check() -> bool:
    """Check database health"""
    return await db_manager.health_check()