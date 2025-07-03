#!/usr/bin/env python3
"""
Script to check what users exist in the MongoDB database.
This script connects to the RAISE database and lists all users in the users collection.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add the backend directory to the path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_dir)

from app.database.mongodb import connect_to_mongo, mongodb_manager, Collections
from app.core.database import db_manager, get_collection

logger = logging.getLogger(__name__)

async def check_users():
    """Check what users exist in the database"""
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        logger.info("Successfully connected to MongoDB")
        
        # Get users collection
        users_collection = get_collection(Collections.USERS)
        
        # Count total users
        total_users = await users_collection.count_documents({})
        logger.info(f"Total users in database: {total_users}")
        
        if total_users == 0:
            logger.info("No users found in the database")
            return
        
        # Get all users
        users_cursor = users_collection.find({})
        users = await users_cursor.to_list(length=None)
        
        logger.info("\n" + "="*60)
        logger.info("USERS IN DATABASE:")
        logger.info("="*60)
        
        for i, user in enumerate(users, 1):
            logger.info(f"\nUser {i}:")
            logger.info(f"  ID: {user.get('_id')}")
            logger.info(f"  Name: {user.get('name', 'N/A')}")
            logger.info(f"  Email: {user.get('email', 'N/A')}")
            logger.info(f"  Role: {user.get('role', 'N/A')}")
            logger.info(f"  Email Verified: {user.get('email_verified', 'N/A')}")
            logger.info(f"  Created At: {user.get('created_at', 'N/A')}")
            logger.info(f"  Updated At: {user.get('updated_at', 'N/A')}")
            
            # Check if password is set
            password_status = "Set" if user.get('password') else "Not Set"
            logger.info(f"  Password: {password_status}")
        
        logger.info("\n" + "="*60)
        
        # Check for the specific user mentioned in logs
        target_email = "ssoysang.work@gmail.com"
        target_user = await users_collection.find_one({"email": target_email})
        
        if target_user:
            logger.info(f"✅ User '{target_email}' FOUND in database")
            logger.info(f"   User ID: {target_user.get('_id')}")
            logger.info(f"   Name: {target_user.get('name', 'N/A')}")
        else:
            logger.info(f"❌ User '{target_email}' NOT FOUND in database")
        
        # Show unique emails for verification
        logger.info("\n" + "="*40)
        logger.info("ALL EMAIL ADDRESSES:")
        logger.info("="*40)
        
        emails = []
        async for user in users_collection.find({}, {"email": 1, "_id": 0}):
            if user.get('email'):
                emails.append(user['email'])
        
        for email in sorted(set(emails)):
            logger.info(f"  • {email}")
        
        logger.info(f"\nTotal unique emails: {len(set(emails))}")
        
    except Exception as e:
        logger.error(f"Error checking users: {e}")
        raise
    finally:
        # Close connection
        await db_manager.disconnect()
        logger.info("Disconnected from MongoDB")

async def check_database_collections():
    """Check what collections exist in the database"""
    try:
        await connect_to_mongo()
        db = db_manager.get_database()
        
        # List all collections
        collections = await db.list_collection_names()
        
        logger.info("\n" + "="*40)
        logger.info("DATABASE COLLECTIONS:")
        logger.info("="*40)
        
        for collection_name in sorted(collections):
            # Get count for each collection
            collection = db[collection_name]
            count = await collection.count_documents({})
            logger.info(f"  • {collection_name}: {count} documents")
        
        logger.info(f"\nTotal collections: {len(collections)}")
        
    except Exception as e:
        logger.error(f"Error checking collections: {e}")
        raise

async def create_test_user():
    """Create a test user for debugging"""
    try:
        await connect_to_mongo()
        users_collection = get_collection(Collections.USERS)
        
        # Check if test user already exists
        test_email = "test@example.com"
        existing_user = await users_collection.find_one({"email": test_email})
        
        if existing_user:
            logger.info(f"Test user {test_email} already exists")
            return
        
        # Create test user
        test_user = {
            "name": "Test User",
            "email": test_email,
            "password": "$2b$12$example_hashed_password",  # This would be properly hashed
            "role": "user",
            "email_verified": None,
            "image": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        result = await users_collection.insert_one(test_user)
        logger.info(f"Created test user with ID: {result.inserted_id}")
        
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        raise

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check users in MongoDB database")
    parser.add_argument("--collections", action="store_true", help="Show all collections")
    parser.add_argument("--create-test", action="store_true", help="Create a test user")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    try:
        if args.collections:
            await check_database_collections()
        
        if args.create_test:
            await create_test_user()
        
        # Always check users
        await check_users()
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)