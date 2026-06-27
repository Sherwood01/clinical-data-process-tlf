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

    # MinIO (S3-compatible file storage — local development)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_PUBLIC_ENDPOINT: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_PREFIX: str = "tlf-saas"
    MINIO_SECURE: bool = False

    # GCS (Google Cloud Storage — production)
    GCS_BUCKET_PREFIX: str = "tlf-saas"
    GCS_LOCATION: str = "US"
    GCS_CREDENTIALS_PATH: str = ""  # Optional, leave empty for Workload Identity

    # SuperTokens (authentication service)
    SUPERTOKENS_CONNECTION_URI: str = "http://supertokens:3567"
    SUPERTOKENS_API_KEY: str = ""
    SUPERTOKENS_API_DOMAIN: str = "http://localhost:8100"
    SUPERTOKENS_WEBSITE_DOMAIN: str = "http://localhost:3000"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # HTTP Worker (Cloud Run mode — replaces Celery)
    WORKER_HTTP_URL: str = ""  # e.g. "https://tlf-worker-xxxxx-uc.a.run.app"

    # OAuth providers (SuperTokens third-party login)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""

    # File size limits
    MAX_UPLOAD_SIZE_MB: int = 500

    # Storage backend: "minio" (local dev) or "gcs" (Cloud Run)
    STORAGE_BACKEND: str = "minio"

    # Creem 计费配置
    CREEM_API_KEY: str = ""  # Creem API 密钥
    CREEM_WEBHOOK_SECRET: str = ""  # Creem Webhook 签名验证密钥

    # Temp directory for worker processing
    WORKER_TEMP_DIR: str = "/tmp/tlf-worker"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra env vars from docker-compose


settings = Settings()
