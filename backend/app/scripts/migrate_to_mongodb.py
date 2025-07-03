"""
Migration script to migrate data from Prisma/PostgreSQL to MongoDB

This script helps migrate existing data when transitioning from Prisma to MongoDB.
Run this script after setting up the new MongoDB infrastructure.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.mongodb import connect_to_mongo, mongodb_manager
from app.core.database import db_manager

logger = logging.getLogger(__name__)

class MongoDBMigration:
    """Handles migration from Prisma to MongoDB"""
    
    def __init__(self):
        self.source_connection = None  # Would be Prisma client
        self.target_collections = {
            'users': mongodb_manager.get_users_collection(),
            'documents': mongodb_manager.get_documents_collection(),
            'document_chunks': mongodb_manager.get_document_chunks_collection(),
            'flashcards': mongodb_manager.get_flashcards_collection(),
            'quizzes': mongodb_manager.get_quizzes_collection(),
            'quiz_attempts': mongodb_manager.get_quiz_attempts_collection(),
            'chat_messages': mongodb_manager.get_chat_messages_collection(),
        }
    
    async def run_migration(self, data_path: Optional[str] = None):
        """Run the complete migration process"""
        try:
            await connect_to_mongo()
            logger.info("Connected to MongoDB")
            
            if data_path:
                # Migrate from JSON files (if you exported Prisma data)
                await self._migrate_from_json(data_path)
            else:
                # Direct migration from Prisma (if still connected)
                await self._migrate_from_prisma()
            
            # Verify migration
            await self._verify_migration()
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def _migrate_from_json(self, data_path: str):
        """Migrate data from JSON exports"""
        import json
        
        # Migrate users
        try:
            with open(f"{data_path}/users.json", 'r') as f:
                users_data = json.load(f)
            await self._migrate_users(users_data)
        except FileNotFoundError:
            logger.warning("users.json not found, skipping users migration")
        
        # Migrate documents
        try:
            with open(f"{data_path}/documents.json", 'r') as f:
                documents_data = json.load(f)
            await self._migrate_documents(documents_data)
        except FileNotFoundError:
            logger.warning("documents.json not found, skipping documents migration")
        
        # Migrate flashcards
        try:
            with open(f"{data_path}/flashcards.json", 'r') as f:
                flashcards_data = json.load(f)
            await self._migrate_flashcards(flashcards_data)
        except FileNotFoundError:
            logger.warning("flashcards.json not found, skipping flashcards migration")
        
        # Migrate quizzes
        try:
            with open(f"{data_path}/quizzes.json", 'r') as f:
                quizzes_data = json.load(f)
            await self._migrate_quizzes(quizzes_data)
        except FileNotFoundError:
            logger.warning("quizzes.json not found, skipping quizzes migration")
        
        # Migrate quiz attempts
        try:
            with open(f"{data_path}/quiz_attempts.json", 'r') as f:
                attempts_data = json.load(f)
            await self._migrate_quiz_attempts(attempts_data)
        except FileNotFoundError:
            logger.warning("quiz_attempts.json not found, skipping quiz attempts migration")
        
        # Migrate chat messages
        try:
            with open(f"{data_path}/chat_messages.json", 'r') as f:
                messages_data = json.load(f)
            await self._migrate_chat_messages(messages_data)
        except FileNotFoundError:
            logger.warning("chat_messages.json not found, skipping chat messages migration")
    
    async def _migrate_from_prisma(self):
        """Direct migration from Prisma (placeholder)"""
        logger.warning("Direct Prisma migration not implemented. Please export your data to JSON first.")
        logger.info("To export data from Prisma:")
        logger.info("1. Create a script to export each model to JSON")
        logger.info("2. Run: python export_prisma_data.py")
        logger.info("3. Then run this migration with the exported data")
    
    async def _migrate_users(self, users_data: List[Dict[str, Any]]):
        """Migrate users data"""
        logger.info(f"Migrating {len(users_data)} users...")
        
        users_collection = self.target_collections['users']
        migrated_users = []
        
        for user in users_data:
            # Convert Prisma user to MongoDB format
            mongo_user = {
                "_id": user["id"],  # Keep original ID if it's ObjectId
                "name": user.get("name"),
                "email": user.get("email"),
                "email_verified": user.get("emailVerified"),
                "image": user.get("image"),
                "password": user.get("password"),
                "role": user.get("role", "user"),
                "created_at": self._parse_datetime(user.get("createdAt")),
                "updated_at": self._parse_datetime(user.get("updatedAt"))
            }
            migrated_users.append(mongo_user)
        
        if migrated_users:
            try:
                await users_collection.insert_many(migrated_users, ordered=False)
                logger.info(f"Successfully migrated {len(migrated_users)} users")
            except Exception as e:
                logger.error(f"Error migrating users: {e}")
    
    async def _migrate_documents(self, documents_data: List[Dict[str, Any]]):
        """Migrate documents data"""
        logger.info(f"Migrating {len(documents_data)} documents...")
        
        documents_collection = self.target_collections['documents']
        migrated_documents = []
        
        for doc in documents_data:
            mongo_doc = {
                "_id": doc["id"],
                "user_id": doc["userId"],
                "title": doc["title"],
                "filename": doc["filename"],
                "content": doc["content"],
                "file_type": doc["fileType"],
                "file_size": doc["fileSize"],
                "upload_path": doc.get("uploadPath"),
                "status": doc.get("status", "processing"),
                "processing_progress": 100 if doc.get("status") == "completed" else 0,
                "error_message": None,
                "created_at": self._parse_datetime(doc.get("createdAt")),
                "updated_at": self._parse_datetime(doc.get("updatedAt"))
            }
            migrated_documents.append(mongo_doc)
        
        if migrated_documents:
            try:
                await documents_collection.insert_many(migrated_documents, ordered=False)
                logger.info(f"Successfully migrated {len(migrated_documents)} documents")
            except Exception as e:
                logger.error(f"Error migrating documents: {e}")
    
    async def _migrate_flashcards(self, flashcards_data: List[Dict[str, Any]]):
        """Migrate flashcards data"""
        logger.info(f"Migrating {len(flashcards_data)} flashcards...")
        
        flashcards_collection = self.target_collections['flashcards']
        migrated_flashcards = []
        
        for card in flashcards_data:
            mongo_card = {
                "_id": card["id"],
                "user_id": card["userId"],
                "document_id": card["documentId"],
                "question": card["question"],
                "answer": card["answer"],
                "difficulty": card.get("difficulty", "medium"),
                "ease_factor": card.get("easeFactor", 2.5),
                "interval": card.get("interval", 1),
                "next_review": self._parse_datetime(card.get("nextReview")),
                "review_count": card.get("reviewCount", 0),
                "correct_count": 0,  # New field, start at 0
                "incorrect_count": 0,  # New field, start at 0
                "created_at": self._parse_datetime(card.get("createdAt")),
                "updated_at": self._parse_datetime(card.get("updatedAt"))
            }
            migrated_flashcards.append(mongo_card)
        
        if migrated_flashcards:
            try:
                await flashcards_collection.insert_many(migrated_flashcards, ordered=False)
                logger.info(f"Successfully migrated {len(migrated_flashcards)} flashcards")
            except Exception as e:
                logger.error(f"Error migrating flashcards: {e}")
    
    async def _migrate_quizzes(self, quizzes_data: List[Dict[str, Any]]):
        """Migrate quizzes data"""
        logger.info(f"Migrating {len(quizzes_data)} quizzes...")
        
        quizzes_collection = self.target_collections['quizzes']
        migrated_quizzes = []
        
        for quiz in quizzes_data:
            mongo_quiz = {
                "_id": quiz["id"],
                "document_id": quiz["documentId"],
                "title": quiz["title"],
                "description": quiz.get("description"),
                "questions": quiz["questions"],
                "total_points": quiz["totalPoints"],
                "time_limit": quiz.get("timeLimit"),
                "attempts_allowed": -1,  # Unlimited by default
                "created_at": self._parse_datetime(quiz.get("createdAt")),
                "updated_at": self._parse_datetime(quiz.get("updatedAt"))
            }
            migrated_quizzes.append(mongo_quiz)
        
        if migrated_quizzes:
            try:
                await quizzes_collection.insert_many(migrated_quizzes, ordered=False)
                logger.info(f"Successfully migrated {len(migrated_quizzes)} quizzes")
            except Exception as e:
                logger.error(f"Error migrating quizzes: {e}")
    
    async def _migrate_quiz_attempts(self, attempts_data: List[Dict[str, Any]]):
        """Migrate quiz attempts data"""
        logger.info(f"Migrating {len(attempts_data)} quiz attempts...")
        
        attempts_collection = self.target_collections['quiz_attempts']
        migrated_attempts = []
        
        for attempt in attempts_data:
            mongo_attempt = {
                "_id": attempt["id"],
                "user_id": attempt["userId"],
                "quiz_id": attempt["quizId"],
                "answers": attempt["answers"],
                "score": attempt["score"],
                "total_points": attempt["totalPoints"],
                "percentage": attempt["percentage"],
                "time_taken": attempt["timeTaken"],
                "bloom_scores": {},  # New field
                "question_results": [],  # New field
                "completed_at": self._parse_datetime(attempt.get("completedAt"))
            }
            migrated_attempts.append(mongo_attempt)
        
        if migrated_attempts:
            try:
                await attempts_collection.insert_many(migrated_attempts, ordered=False)
                logger.info(f"Successfully migrated {len(migrated_attempts)} quiz attempts")
            except Exception as e:
                logger.error(f"Error migrating quiz attempts: {e}")
    
    async def _migrate_chat_messages(self, messages_data: List[Dict[str, Any]]):
        """Migrate chat messages data"""
        logger.info(f"Migrating {len(messages_data)} chat messages...")
        
        messages_collection = self.target_collections['chat_messages']
        migrated_messages = []
        
        for message in messages_data:
            mongo_message = {
                "_id": message["id"],
                "user_id": message["userId"],
                "document_id": message["documentId"],
                "session_id": None,  # New field
                "question": message["question"],
                "answer": message["answer"],
                "sources": message.get("sources", []),
                "confidence": message.get("confidence"),
                "created_at": self._parse_datetime(message.get("createdAt"))
            }
            migrated_messages.append(mongo_message)
        
        if migrated_messages:
            try:
                await messages_collection.insert_many(migrated_messages, ordered=False)
                logger.info(f"Successfully migrated {len(migrated_messages)} chat messages")
            except Exception as e:
                logger.error(f"Error migrating chat messages: {e}")
    
    async def _verify_migration(self):
        """Verify the migration was successful"""
        logger.info("Verifying migration...")
        
        for collection_name, collection in self.target_collections.items():
            count = await collection.count_documents({})
            logger.info(f"{collection_name}: {count} documents")
        
        # Check indexes
        await self._verify_indexes()
    
    async def _verify_indexes(self):
        """Verify that all indexes are created"""
        logger.info("Verifying indexes...")
        
        for collection_name, collection in self.target_collections.items():
            indexes = await collection.list_indexes().to_list(None)
            index_names = [idx['name'] for idx in indexes]
            logger.info(f"{collection_name} indexes: {index_names}")
    
    def _parse_datetime(self, dt_str: Any) -> datetime:
        """Parse datetime string to datetime object"""
        if dt_str is None:
            return datetime.datetime.utcnow()
        
        if isinstance(dt_str, datetime):
            return dt_str
        
        if isinstance(dt_str, str):
            try:
                # Try parsing ISO format
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            except:
                # Fallback to current time
                return datetime.datetime.utcnow()
        
        return datetime.datetime.utcnow()

async def create_sample_data():
    """Create sample data for testing (optional)"""
    logger.info("Creating sample data...")
    
    await connect_to_mongo()
    
    # Sample user
    users_collection = mongodb_manager.get_users_collection()
    sample_user = {
        "name": "Test User",
        "email": "test@example.com",
        "email_verified": None,
        "image": None,
        "password": "$2b$12$hash",  # Hashed password
        "role": "user",
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }
    
    user_result = await users_collection.insert_one(sample_user)
    user_id = user_result.inserted_id
    
    # Sample document
    documents_collection = mongodb_manager.get_documents_collection()
    sample_document = {
        "user_id": user_id,
        "title": "Sample Document",
        "filename": "sample.txt",
        "content": "This is a sample document for testing the MongoDB migration.",
        "file_type": "txt",
        "file_size": 1024,
        "upload_path": None,
        "status": "completed",
        "processing_progress": 100,
        "error_message": None,
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }
    
    doc_result = await documents_collection.insert_one(sample_document)
    logger.info(f"Created sample user {user_id} and document {doc_result.inserted_id}")

async def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate from Prisma to MongoDB")
    parser.add_argument("--data-path", help="Path to exported JSON data")
    parser.add_argument("--create-sample", action="store_true", help="Create sample data")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing data")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        if args.create_sample:
            await create_sample_data()
        elif args.verify_only:
            migration = MongoDBMigration()
            await connect_to_mongo()
            await migration._verify_migration()
        else:
            migration = MongoDBMigration()
            await migration.run_migration(args.data_path)
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)