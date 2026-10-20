import os
from pathlib import Path
from typing import Optional
from app.config import settings
from app.logging_config import logger


class StorageService:
    """Manages S3-compatible / MinIO cloud storage and local fallback (Integration Standard 7)."""

    _client = None
    _bucket_initialized = False

    @classmethod
    def get_client(cls):
        """Lazy-initializes Minio client when S3 is enabled."""
        if cls._client is None and settings.S3_ENABLED:
            try:
                from minio import Minio

                endpoint = settings.S3_ENDPOINT.replace("http://", "").replace("https://", "")
                cls._client = Minio(
                    endpoint=endpoint,
                    access_key=settings.S3_ACCESS_KEY,
                    secret_key=settings.S3_SECRET_KEY,
                    secure=settings.S3_USE_SSL,
                )
                logger.info("Initialized S3/MinIO storage client at %s", settings.S3_ENDPOINT)
            except Exception as e:
                logger.warning("Could not initialize S3/MinIO client: %s. Using local storage.", str(e))
                cls._client = None
        return cls._client

    @classmethod
    def ensure_bucket(cls) -> bool:
        """Ensures the destination S3 bucket exists."""
        client = cls.get_client()
        if client is None:
            return False

        if not cls._bucket_initialized:
            try:
                if not client.bucket_exists(settings.S3_BUCKET):
                    client.make_bucket(settings.S3_BUCKET)
                    logger.info("Created S3/MinIO bucket: %s", settings.S3_BUCKET)
                cls._bucket_initialized = True
            except Exception as e:
                logger.warning("Error checking/creating S3 bucket %s: %s", settings.S3_BUCKET, str(e))
                return False
        return True

    @classmethod
    def upload_output(cls, local_path: str, object_name: Optional[str] = None) -> str:
        """
        Uploads a rendered media or export file to S3/MinIO if enabled.
        Returns the S3 URL / presigned link, or falls back to /api/v1/media/{filename}.
        """
        p = Path(local_path)
        if not p.exists():
            return f"/api/v1/media/{p.name}"

        obj_name = object_name or p.name

        # If S3 is enabled, attempt upload
        if settings.S3_ENABLED and cls.ensure_bucket():
            client = cls.get_client()
            if client:
                try:
                    content_type = "video/mp4" if p.suffix.lower() == ".mp4" else "application/octet-stream"
                    client.fput_object(
                        bucket_name=settings.S3_BUCKET,
                        object_name=obj_name,
                        file_path=str(p),
                        content_type=content_type,
                    )
                    logger.info("Uploaded output to S3/MinIO: %s/%s", settings.S3_BUCKET, obj_name)

                    scheme = "https" if settings.S3_USE_SSL else "http"
                    s3_url = f"{scheme}://{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{obj_name}"
                    return s3_url
                except Exception as e:
                    logger.warning("Failed S3 upload for %s: %s. Falling back to local URL.", p.name, str(e))

        # Default local download route
        return f"/api/v1/media/{p.name}"


storage_service = StorageService
