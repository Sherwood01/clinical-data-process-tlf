"""Application configuration via environment variables."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "TLF Report Generator API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8100
    CORS_ORIGINS: str = "http://localhost:3100"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tlf_saas"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres@localhost:5432/tlf_saas"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO (S3-compatible file storage)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_PUBLIC_ENDPOINT: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_PREFIX: str = "tlf-saas"
    MINIO_SECURE: bool = False

    # Stack Auth JWT
    STACK_AUTH_JWKS_URL: str = "http://stack-auth:8102/api/latest/projects/internal/.well-known/jwks.json"
    STACK_AUTH_ISSUER: str = "http://stack-auth:8102/api/v1/projects/internal"
    STACK_AUTH_AUDIENCE: str = "internal"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # File size limits
    MAX_UPLOAD_SIZE_MB: int = 500

    # Temp directory for worker processing
    WORKER_TEMP_DIR: str = "/tmp/tlf-worker"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra env vars from docker-compose


settings = Settings()
