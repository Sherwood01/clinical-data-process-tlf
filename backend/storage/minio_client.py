"""MinIO (S3-compatible) storage client wrapper.

NOTE: The underlying ``minio`` library is synchronous. Async wrappers (``async def``)
are provided for the FastAPI async context. Sync aliases (``*_sync``) are provided for
the Celery worker / orchestrator which run in a synchronous context.
"""
import hashlib
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from backend.core.config import settings


class MinioStorage:
    """Abstraction over MinIO for file upload/download with tenant isolation."""

    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

    # ── Helpers (sync, used by both async and sync callers) ──

    def _bucket_name(self, tenant_id: str) -> str:
        sanitized = tenant_id.replace("-", "").lower()[:50]
        return f"{settings.MINIO_BUCKET_PREFIX}-{sanitized}"

    def _object_key(self, study_id: str, resource: str, filename: str) -> str:
        return f"studies/{study_id}/{resource}/{filename}"

    def _ensure_bucket_sync(self, tenant_id: str):
        bucket = self._bucket_name(tenant_id)
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

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
        bucket = self._bucket_name(tenant_id)
        object_key = self._object_key(study_id, resource, filename)
        
        # 为了防止浏览器上传时因为 Host Header (如 localhost:9000) 与签名计算 Host (如 minio:9000) 不一致返回 403 Forbidden，
        # 我们必须使用一个 endpoint 配置为公共 Endpoint (public) 的临时客户端来进行本地离线签名计算。
        public = settings.MINIO_PUBLIC_ENDPOINT
        if public:
            endpoint_host = public.replace("http://", "").replace("https://", "")
            secure = public.startswith("https://")
            signing_client = Minio(
                endpoint=endpoint_host,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=secure,
                region="us-east-1",  # 显式指定区域以避免向本地终结点发起获取区域的网络请求
            )
            url = signing_client.presigned_put_object(bucket, object_key, expires=timedelta(seconds=expiry_seconds))
        else:
            url = self.client.presigned_put_object(bucket, object_key, expires=timedelta(seconds=expiry_seconds))
        return url

    async def get_presigned_download_url(
        self,
        tenant_id: str,
        object_key: str,
        expiry_seconds: int = 3600,
    ) -> str:
        bucket = self._bucket_name(tenant_id)
        
        # 同样，对于下载预签名 URL 也使用公共 Endpoint 客户端计算签名，并指定区域以防止网络请求
        public = settings.MINIO_PUBLIC_ENDPOINT
        if public:
            endpoint_host = public.replace("http://", "").replace("https://", "")
            secure = public.startswith("https://")
            signing_client = Minio(
                endpoint=endpoint_host,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=secure,
                region="us-east-1",  # 指定区域避开网络请求
            )
            url = signing_client.presigned_get_object(
                bucket, object_key, expires=timedelta(seconds=expiry_seconds),
                response_headers={"response-content-disposition": "inline"}
            )
        else:
            url = self.client.presigned_get_object(
                bucket, object_key, expires=timedelta(seconds=expiry_seconds),
                response_headers={"response-content-disposition": "inline"}
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
        bucket = self._bucket_name(tenant_id)
        try:
            self.client.stat_object(bucket, object_key)
            return True
        except S3Error:
            return False

    async def compute_checksum(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    async def delete_file(self, tenant_id: str, object_key: str):
        bucket = self._bucket_name(tenant_id)
        self.client.remove_object(bucket, object_key)

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
        bucket = self._bucket_name(tenant_id)
        object_key = self._object_key(study_id, resource, filename)
        self.client.put_object(
            bucket_name=bucket,
            object_name=object_key,
            data=data,
            length=length,
            content_type=content_type,
        )
        return object_key

    def download_file_sync(self, tenant_id: str, object_key: str) -> bytes:
        bucket = self._bucket_name(tenant_id)
        response = self.client.get_object(bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()


# Singleton — used by both FastAPI (async) and Celery (sync) contexts
storage = MinioStorage()
