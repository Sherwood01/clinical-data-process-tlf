"""Storage backend factory — selects MinIO (local) or GCS (Cloud Run) based on config."""
from backend.core.config import settings


def _get_storage():
    """Return the appropriate storage singleton based on STORAGE_BACKEND config."""
    backend = settings.STORAGE_BACKEND.lower()
    if backend == "gcs":
        from backend.storage.gcs_client import GCSStorage
        return GCSStorage()
    else:
        from backend.storage.minio_client import MinioStorage
        return MinioStorage()


# Singleton — used by both FastAPI (async) and Celery (sync) contexts
storage = _get_storage()
