# RAISE Backend - MongoDB Migration Guide

This guide covers the complete migration from Prisma ORM to pure MongoDB using Motor (async MongoDB driver) for the RAISE learning platform.

## ✅ Migration Status: COMPLETED

All major components have been successfully migrated to MongoDB:

### ✅ Completed Components

1. **Database Connection** (`app/core/database.py`)
   - Motor AsyncIOMotorClient with connection pooling
   - Health check functionality
   - Transaction support
   - Graceful connection lifecycle management

2. **MongoDB Collections** (`app/database/mongodb.py`)
   - Collection schema definitions
   - Index creation for performance
   - Document validation helpers
   - Migration utilities

3. **Authentication System** (`app/core/auth.py`, `app/services/auth_service.py`)
   - User CRUD operations with MongoDB
   - JWT token handling
   - Password hashing with bcrypt
   - Proper ObjectId handling

4. **Document Management** (`app/services/document_service.py`)
   - Document storage and retrieval
   - File metadata management
   - Processing status tracking
   - Document chunk storage for vector search

5. **Vector Search** (`app/core/vector_search.py`)
   - MongoDB Atlas Vector Search support
   - FAISS fallback for local development
   - Similarity search operations
   - Embedding storage and retrieval

6. **RAG Service** (`app/services/rag_service.py`)
   - Question answering with document context
   - Chat history management
   - Source attribution and confidence scoring
   - Vector similarity search integration

7. **Flashcard System** (`app/services/flashcard_service.py`)
   - Spaced repetition algorithm (SM-2)
   - Review scheduling and tracking
   - Progress analytics
   - CRUD operations

8. **Quiz System** (`app/services/quiz_generator.py`)
   - Quiz generation and management
   - Bloom's taxonomy integration
   - Attempt tracking and scoring
   - Analytics and recommendations

9. **Models and Schemas** (`app/models/`)
   - Updated Pydantic models for MongoDB
   - Proper field mapping and validation
   - Response models for API consistency

10. **Migration Tools** (`app/scripts/migrate_to_mongodb.py`)
    - Data migration from Prisma to MongoDB
    - Sample data creation
    - Migration verification
    - Index validation

## 🗄️ Database Schema

### Collections Structure

```javascript
// Users Collection
{
  "_id": ObjectId,
  "name": String,
  "email": String,  // unique index
  "email_verified": Date,
  "image": String,
  "password": String,  // hashed
  "role": String,
  "created_at": Date,
  "updated_at": Date
}

// Documents Collection
{
  "_id": ObjectId,
  "user_id": ObjectId,  // index
  "title": String,
  "filename": String,
  "content": String,
  "file_type": String,
  "file_size": Number,
  "upload_path": String,
  "status": String,
  "processing_progress": Number,
  "error_message": String,
  "created_at": Date,
  "updated_at": Date
}

// Document Chunks Collection (Vector Search)
{
  "_id": ObjectId,
  "document_id": ObjectId,  // index
  "chunk_index": Number,
  "text": String,
  "embedding": [Number],  // vector array
  "start_pos": Number,
  "end_pos": Number,
  "created_at": Date
}

// Flashcards Collection
{
  "_id": ObjectId,
  "user_id": ObjectId,  // index
  "document_id": ObjectId,  // index
  "question": String,
  "answer": String,
  "difficulty": String,
  "ease_factor": Number,
  "interval": Number,
  "next_review": Date,  // index
  "review_count": Number,
  "correct_count": Number,
  "incorrect_count": Number,
  "created_at": Date,
  "updated_at": Date
}

// Quizzes Collection
{
  "_id": ObjectId,
  "document_id": ObjectId,  // index
  "title": String,
  "description": String,
  "questions": [Object],
  "total_points": Number,
  "time_limit": Number,
  "attempts_allowed": Number,
  "created_at": Date,
  "updated_at": Date
}

// Quiz Attempts Collection
{
  "_id": ObjectId,
  "user_id": ObjectId,  // index
  "quiz_id": ObjectId,  // index
  "answers": [String],
  "score": Number,
  "total_points": Number,
  "percentage": Number,
  "time_taken": Number,
  "bloom_scores": Object,
  "question_results": [Object],
  "completed_at": Date
}

// Chat Messages Collection
{
  "_id": ObjectId,
  "user_id": ObjectId,  // index
  "document_id": ObjectId,  // index
  "session_id": String,
  "question": String,
  "answer": String,
  "sources": [Object],
  "confidence": Number,
  "created_at": Date
}
```

## 🔧 Environment Configuration

Add these environment variables to your `.env` file:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/raise_db
MONGODB_DB_NAME=raise_db
MONGODB_MAX_CONNECTIONS=50
MONGODB_MIN_CONNECTIONS=5

# Vector Search (MongoDB Atlas)
MONGODB_VECTOR_SEARCH_INDEX=vector_index

# Or for local development with FAISS
USE_FAISS_VECTOR_SEARCH=true
```

## 📦 Dependencies

Updated `requirements.txt` includes:

```txt
# Database - MongoDB with Motor
motor>=3.3.0
pymongo>=4.5.0

# Vector Search (optional)
faiss-cpu>=1.7.4  # For local vector search fallback
```

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file with the MongoDB configuration above.

### 3. Run Migration (Optional)

If you have existing Prisma data:

```bash
# Create sample data for testing
python app/scripts/migrate_to_mongodb.py --create-sample

# Or migrate from exported JSON data
python app/scripts/migrate_to_mongodb.py --data-path /path/to/exported/data

# Verify migration
python app/scripts/migrate_to_mongodb.py --verify-only
```

### 4. Start the Application

```bash
python app/main.py
```

The application will:
- Connect to MongoDB
- Create necessary indexes
- Initialize vector search
- Start the FastAPI server

## 🔍 Key Features

### 1. Connection Management
- Singleton pattern with connection pooling
- Automatic reconnection handling
- Health check endpoints
- Graceful shutdown

### 2. Vector Search
- MongoDB Atlas Vector Search for production
- FAISS fallback for local development
- Configurable similarity thresholds
- Efficient batch operations

### 3. Document Processing
- Chunking for large documents
- Vector embedding storage
- Processing status tracking
- Error handling and recovery

### 4. Spaced Repetition
- SM-2 algorithm implementation
- Adaptive difficulty adjustment
- Review scheduling optimization
- Progress analytics

### 5. Performance Optimizations
- Strategic indexing for common queries
- Connection pooling
- Async operations throughout
- Efficient aggregation pipelines

## 🛠️ API Compatibility

The MongoDB migration maintains full API compatibility with the existing frontend. All endpoints return the same response formats, ensuring no changes are needed in the client application.

### Response Format Example

```json
{
  "success": true,
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "title": "Sample Document",
    "status": "completed",
    "createdAt": "2024-01-15T10:30:00Z"
  },
  "message": "Operation successful",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔧 Troubleshooting

### Common Issues

1. **Connection Failed**
   ```bash
   # Check MongoDB is running
   mongosh --eval "db.adminCommand('ping')"
   ```

2. **Index Creation Failed**
   ```bash
   # Verify index creation
   python app/scripts/migrate_to_mongodb.py --verify-only
   ```

3. **Vector Search Not Working**
   ```bash
   # Check FAISS installation
   pip install faiss-cpu
   
   # Or configure Atlas Vector Search
   export MONGODB_VECTOR_SEARCH_INDEX=vector_index
   ```

### Performance Tuning

1. **Connection Pool Size**
   ```bash
   export MONGODB_MAX_CONNECTIONS=100
   export MONGODB_MIN_CONNECTIONS=10
   ```

2. **Vector Search Optimization**
   ```bash
   # Use Atlas Vector Search for production
   export MONGODB_VECTOR_SEARCH_INDEX=vector_index
   export USE_FAISS_VECTOR_SEARCH=false
   ```

## 📊 Monitoring

The application includes comprehensive health checks:

- **GET /health**: Basic health and database connectivity
- Database connection status
- Collection count verification
- Index status monitoring

## 🔒 Security

Security features implemented:

- Proper ObjectId validation
- Input sanitization
- Password hashing with bcrypt
- JWT token validation
- Rate limiting support
- CORS configuration

## 🚀 Production Deployment

For production deployment:

1. Use MongoDB Atlas for managed hosting
2. Configure Vector Search indexes in Atlas
3. Set up proper connection pooling
4. Enable authentication and SSL
5. Configure monitoring and alerts

## 📈 Performance Metrics

Expected performance improvements:

- **Query Speed**: Sub-second response times
- **Concurrent Users**: Support for 1000+ users
- **Vector Search**: Efficient similarity operations
- **Memory Usage**: Optimized for production workloads

The MongoDB migration is now complete and ready for production use! 🎉