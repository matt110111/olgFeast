from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "olgFeast API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "sqlite:///./fastapi_olgfeast.db"
    # For production: "postgresql://user:password@localhost/olgfeast"
    
    # Authentication
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # CORS
    ALLOWED_HOSTS: list = ["*"]
    
    # Redis (for WebSocket channels)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    BCRYPT_ROUNDS: int = 12
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
