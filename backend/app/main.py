from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
import logging
import sys
from pathlib import Path
import os

from app.config import settings
from app.database.mongodb import connect_to_mongo, close_mongo_connection
from app.core.vector_search import initialize_vector_search
from app.core.database import database_health_check
from app.routers import documents, flashcards, quiz, chat, analytics, auth
from app.core.exceptions import setup_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log') if Path('logs').exists() else logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting RAISE application in {settings.environment} environment")
    try:
        await connect_to_mongo()
        await initialize_vector_search()
        logger.info("✅ MongoDB and vector search initialized successfully")
        
        # Log important configuration for debugging (without sensitive data)
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"Database: {settings.database_name}")
        logger.info(f"Allowed origins: {settings.allowed_origins}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await close_mongo_connection()
        logger.info("✅ Database connection closed successfully")
    except Exception as e:
        logger.error(f"❌ Error closing database connection: {e}")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-powered learning platform backend with RAG technology",
    lifespan=lifespan,
    debug=settings.debug,
    # Disable docs in production for security
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    # Additional security headers
    expose_headers=["X-Total-Count", "X-Page-Count"] if settings.debug else [],
)

# Trust only specific hosts in production
if settings.is_production:
    trusted_hosts = ["*.vercel.app", "*.herokuapp.com", "*.railway.app"]
    # Extract domains from allowed origins
    for origin in settings.allowed_origins:
        if origin.startswith("https://"):
            domain = origin.replace("https://", "")
            trusted_hosts.append(domain)
        elif origin.startswith("http://"):
            domain = origin.replace("http://", "")
            trusted_hosts.append(domain)
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=trusted_hosts
    )
else:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "*.vercel.app"]
    )

# Exception handlers
setup_exception_handlers(app)

# Include routers with proper authentication
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(flashcards.router, prefix="/api/flashcards", tags=["flashcards"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    return {
        "success": True,
        "message": "RAISE Backend API is running",
        "version": settings.version,
        "environment": settings.environment,
        "docs_url": "/docs" if not settings.is_production else "Documentation disabled in production",
        "timestamp": "2024-01-15T10:30:00Z"
    }


@app.get("/health")
async def health_check():
    """Enhanced health check with database status"""
    try:
        db_healthy = await database_health_check()
        
        return {
            "success": True,
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
            "environment": settings.environment,
            "version": settings.version,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "database": "error",
            "error": str(e) if settings.debug else "Internal server error",
            "timestamp": "2024-01-15T10:30:00Z"
        }


@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "success": True,
        "api": {
            "name": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "debug": settings.debug
        },
        "endpoints": {
            "authentication": "/api/auth",
            "documents": "/api/documents",
            "flashcards": "/api/flashcards",
            "quiz": "/api/quiz",
            "chat": "/api/chat",
            "analytics": "/api/analytics"
        },
        "timestamp": "2024-01-15T10:30:00Z"
    }


if __name__ == "__main__":
    # Production-ready uvicorn configuration
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.debug and not settings.is_production,  # Only enable reload in development
        workers=1 if settings.debug else int(os.getenv("WORKERS", 4)),
        access_log=settings.debug,
        use_colors=settings.debug,
        log_level="debug" if settings.debug else "info",
        # Additional production settings
        limit_concurrency=int(os.getenv("LIMIT_CONCURRENCY", 1000)),
        limit_max_requests=int(os.getenv("LIMIT_MAX_REQUESTS", 10000)),
        timeout_keep_alive=int(os.getenv("TIMEOUT_KEEP_ALIVE", 30)),
        # File upload settings - support large files up to 100MB
        h11_max_incomplete_event_size=100 * 1024 * 1024,  # 100MB
    )