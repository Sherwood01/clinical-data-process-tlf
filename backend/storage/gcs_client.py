"""Google Cloud Storage client wrapper.

Provides the same interface as MinioStorage for drop-in replacement.
- Cloud Run: uses Workload Identity (no explicit credentials needed)
- Local dev: uses GOOGLE_APPLICATION_CREDENTIALS or gcloud auth
"""
import hashlib
from datetime import timedelta, datetime
from pathlib import Path
from typing import BinaryIO, Optional

from google.cloud import storage as gcs
from google.cloud.storage.retry import DEFAULT_RETRY

from backend.core.config import settings


class GCSStorage:
    """Abstraction over GCS for file upload/download with tenant isolation."""

    def __init__(self):
        if settings.GCS_CREDENTIALS_PATH:
            self.client = gcs.Client.from_service_account_json(settings.GCS_CREDENTIALS_PATH)
        else:
            self.client = gcs.Client()

    # ── Helpers (sync, used by both async and sync callers) ──

    def _bucket_name(self, tenant_id: str) -> str:
        sanitized = tenant_id.replace("-", "").lower()[:50]
        return f"{settings.GCS_BUCKET_PREFIX}-{sanitized}"

    def _object_key(self, study_id: str, resource: str, filename: str) -> str:
        return f"studies/{study_id}/{resource}/{filename}"

    def _ensure_bucket_sync(self, tenant_id: str):
        bucket_name = self._bucket_name(tenant_id)
        try:
            self.client.get_bucket(bucket_name)
        except Exception:
            self.client.create_bucket(bucket_name, location=settings.GCS_LOCATION or "US")

    def _get_bucket(self, tenant_id: str):
        bucket_name = self._bucket_name(tenant_id)
        return self.client.bucket(bucket_name)

    # ── Async methods (for FastAPI routers) ──

    async def ensure_bucket(self, tenant_id: str):
        self._ensure_bucket_sync(tenant_id)

    async def get_presigned_upload_url(
        self,
        tenant_id: str,
        study_id: str,
        resource: str,
        filename: str,
        expiry_seconds: int = 3600,
    ) -> str:
        self._ensure_bucket_sync(tenant_id)
        bucket = self._get_bucket(tenant_id)
        object_key = self._object_key(study_id, resource, filename)
        blob = bucket.blob(object_key)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiry_seconds),
            method="PUT",
        )
        return url

    async def get_presigned_download_url(
        self,
        tenant_id: str,
        object_key: str,
        expiry_seconds: int = 3600,
    ) -> str:
        bucket = self._get_bucket(tenant_id)
        blob = bucket.blob(object_key)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiry_seconds),
            method="GET",
            response_disposition="inline",
        )
        return url

    async def upload_file(
        self,
        tenant_id: str,
        study_id: str,
        resource: str,
        filename: str,
        data: BinaryIO,
        length: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        return self.upload_file_sync(tenant_id, study_id, resource, filename, data, length, content_type)

    async def download_file(self, tenant_id: str, object_key: str) -> bytes:
        return self.download_file_sync(tenant_id, object_key)

    async def download_to_temp(self, tenant_id: str, object_key: str, temp_path: Path):
        data = self.download_file_sync(tenant_id, object_key)
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_bytes(data)

    async def file_exists(self, tenant_id: str, object_key: str) -> bool:
        bucket = self._get_bucket(tenant_id)
        blob = bucket.blob(object_key)
        return blob.exists()

    async def compute_checksum(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    async def delete_file(self, tenant_id: str, object_key: str):
        bucket = self._get_bucket(tenant_id)
        blob = bucket.blob(object_key)
        blob.delete()

    # ── Sync methods (for Celery worker / orchestrator) ──

    def upload_file_sync(
        self,
        tenant_id: str,
        study_id: str,
        resource: str,
        filename: str,
        data: BinaryIO,
        length: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        self._ensure_bucket_sync(tenant_id)
        bucket = self._get_bucket(tenant_id)
        object_key = self._object_key(study_id, resource, filename)
        blob = bucket.blob(object_key)
        blob.upload_from_file(data, content_type=content_type, retry=DEFAULT_RETRY)
        return object_key

    def download_file_sync(self, tenant_id: str, object_key: str) -> bytes:
        bucket = self._get_bucket(tenant_id)
        blob = bucket.blob(object_key)
        return blob.download_as_bytes(retry=DEFAULT_RETRY)


# Singleton — used by both FastAPI (async) and Celery (sync) contexts
storage = GCSStorage()
