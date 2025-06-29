from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    app_name: str = "RAISE Backend API"
    version: str = "1.0.0"
    debug: bool = False
    
    # Database Configuration
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "raise_db")
    
    # AI Model Configuration
    together_ai_api_key: str = os.getenv("TOGETHER_AI_API_KEY", "")
    llamaparse_api_key: str = os.getenv("LLAMAPARSE_API_KEY", "")
    
    # Model Settings
    llm_model: str = "meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo"
    embedding_model: str = "BAAI/bge-m3"
    max_tokens: int = 2048
    temperature: float = 0.7
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File Upload Settings
    max_file_size: int = 20 * 1024 * 1024  # 20MB
    allowed_file_types: list = ["pdf", "docx", "txt"]
    upload_dir: str = "uploads"
    
    # API Rate Limiting
    requests_per_minute: int = 60
    
    # CORS Settings
    allowed_origins: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000"
    ]
    
    class Config:
        env_file = ".env"

settings = Settings()