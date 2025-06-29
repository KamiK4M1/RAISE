from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import Optional, List, Union
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Configuration
    app_name: str = "RAISE Backend API"
    version: str = "1.0.0"
    debug: bool = False
    
    # Database Configuration
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "raise_db"
    
    # AI Model Configuration
    together_ai_api_key: str = ""
    llamaparse_api_key: str = ""
    
    # Model Settings
    llm_model: str = "meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo"
    embedding_model: str = "BAAI/bge-m3"
    max_tokens: int = 2048
    temperature: float = 0.7
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File Upload Settings
    max_file_size: int = 20 * 1024 * 1024  # 20MB
    allowed_file_types: List[str] = ["pdf", "docx", "txt"]
    upload_dir: str = "uploads"
    
    # API Rate Limiting
    requests_per_minute: int = 60
    
    # CORS Settings
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000"
    ]
    
    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated string into list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @field_validator('debug', mode='before')
    @classmethod
    def parse_debug(cls, v):
        """Parse string boolean values"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v

settings = Settings()