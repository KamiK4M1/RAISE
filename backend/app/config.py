from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import Optional, List, Union
import os
from dotenv import load_dotenv
import secrets

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
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")  # development, staging, production
    
    # Database Configuration
    mongodb_uri: str = Field(default="mongodb://localhost:27017", env="MONGODB_URI")
    database_name: str = Field(default="raise_db", env="MONGODB_DB_NAME")
    mongodb_max_connections: int = Field(default=50, env="MONGODB_MAX_CONNECTIONS")
    mongodb_min_connections: int = Field(default=5, env="MONGODB_MIN_CONNECTIONS")
    
    # Vector Search Configuration
    mongodb_vector_search_index: Optional[str] = Field(default=None, env="MONGODB_VECTOR_SEARCH_INDEX")
    use_faiss_vector_search: bool = Field(default=False, env="USE_FAISS_VECTOR_SEARCH")
    
    # AI Model Configuration
    together_ai_api_key: str = Field(default="", env="TOGETHER_AI_API_KEY")
    llamaparse_api_key: str = Field(default="", env="LLAMAPARSE_API_KEY")
    
    # Embedding Service Configuration
    embedding_endpoint_url: str = Field(default="", env="EMBEDDING_ENDPOINT_URL")
    hf_auth_token: Optional[str] = Field(default=None, env="HF_AUTH_TOKEN")
    
    # Model Settings
    llm_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
    embedding_model: str = "BAAI/bge-m3"
    max_tokens: int = 2048
    temperature: float = 0.7
    
    # Security - Load from environment or generate secure default
    secret_key: str = Field(default_factory=lambda: os.getenv("SECRET_KEY") or secrets.token_urlsafe(32), env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 hours
    
    # File Upload Settings
    max_file_size: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    allowed_file_types: List[str] = ["pdf", "docx", "txt"]
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    
    # API Rate Limiting
    requests_per_minute: int = Field(default=60, env="REQUESTS_PER_MINUTE")
    
    # CORS Settings
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://localhost:3000"
        ],
        env="ALLOWED_ORIGINS"
    )
    
    # Production Security Settings
    secure_cookies: bool = Field(default=False, env="SECURE_COOKIES")  # Set to True in production with HTTPS
    cookie_samesite: str = Field(default="lax", env="COOKIE_SAMESITE")  # lax, strict, none
    
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
    
    @field_validator('secure_cookies', mode='before')
    @classmethod
    def parse_secure_cookies(cls, v):
        """Parse string boolean values"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        """Ensure secret key is sufficiently long"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"

# Validate critical settings on startup
def validate_production_settings(settings: Settings):
    """Validate critical settings for production deployment"""
    if settings.is_production:
        critical_env_vars = [
            "SECRET_KEY",
            "MONGODB_URI",
            "TOGETHER_AI_API_KEY"
        ]
        
        missing_vars = []
        for var in critical_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables for production: {', '.join(missing_vars)}")
        
        # Additional production checks
        if settings.debug:
            raise ValueError("DEBUG must be False in production")
        
        if not settings.secure_cookies and "https" in str(settings.allowed_origins):
            print("Warning: SECURE_COOKIES should be True when using HTTPS in production")

settings = Settings()

# Validate settings on import
if settings.environment:
    validate_production_settings(settings)