from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.config import settings
from app.database.mongodb import connect_to_mongo, close_mongo_connection
from app.routers import documents, flashcards, quiz, chat, analytics
from app.core.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-powered learning platform backend with RAG technology",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app"]
)

# Exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(flashcards.router, prefix="/api/flashcards", tags=["flashcards"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/")
async def root():
    return {
        "success": True,
        "message": "RAISE Backend API is running",
        "version": settings.version,
        "timestamp": "2024-01-15T10:30:00Z"
    }


@app.get("/health")
async def health_check():
    return {
        "success": True,
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )