"""
Core configuration settings for the SoleCraft API.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, EmailStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Settings
    app_name: str = Field(default="SoleCraft API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/solecraft",
        env="DATABASE_URL",
        description="Async PostgreSQL database URL"
    )
    database_url_sync: str = Field(
        default="postgresql://postgres:password@localhost:5432/solecraft",
        env="DATABASE_URL_SYNC",
        description="Sync PostgreSQL database URL for Alembic"
    )
    
    # JWT Configuration
    jwt_secret_key: str = Field(default="dev-jwt-secret-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    
    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # RabbitMQ Configuration (alternative to Redis for Celery)
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", env="RABBITMQ_URL")
    
    # Email Configuration (SendGrid)
    sendgrid_api_key: str = Field(default="", env="SENDGRID_API_KEY")
    email_from: str = Field(default="noreply@solecraft.com", env="EMAIL_FROM")
    email_from_name: str = Field(default="SoleCraft", env="EMAIL_FROM_NAME")
    admin_email: str = Field(default="admin@solecraft.com", env="ADMIN_EMAIL")
    
    # Frontend Configuration
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    
    # File Upload Configuration
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=5242880, env="MAX_FILE_SIZE")  # 5MB
    
    # Pagination
    default_page_size: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Payment Configuration (Stripe)
    stripe_public_key: Optional[str] = Field(default=None, env="STRIPE_PUBLIC_KEY")
    stripe_secret_key: Optional[str] = Field(default=None, env="STRIPE_SECRET_KEY")
    stripe_webhook_secret: Optional[str] = Field(default=None, env="STRIPE_WEBHOOK_SECRET")
    
    # Sentry Configuration
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields to prevent validation errors


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings() 