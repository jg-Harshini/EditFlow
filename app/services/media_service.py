import hashlib
import ipaddress
import os
import shutil
import socket
import urllib.parse
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import httpx
from app.config import settings
from app.engine.renderer import VideoRenderer
from app.logging_config import logger
from app.models.timeline import SourceMedia


class MediaValidationError(Exception):
    """Raised when media ingestion or validation fails."""
    pass


class MediaService:
    """Handles media ingestion, SSRF-safe URL fetching, validation, and SHA-256 calculation."""

    BLOCKED_IP_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),      # Loopback
        ipaddress.ip_network("10.0.0.0/8"),       # Private RFC 1918
        ipaddress.ip_network("172.16.0.0/12"),    # Private RFC 1918
        ipaddress.ip_network("192.168.0.0/16"),   # Private RFC 1918
        ipaddress.ip_network("169.254.0.0/16"),   # Link-local / Cloud Metadata
        ipaddress.ip_network("::1/128"),          # IPv6 Loopback
        ipaddress.ip_network("fc00::/7"),         # IPv6 Unique Local
        ipaddress.ip_network("fe80::/10"),        # IPv6 Link-local
    ]

    @classmethod
    def validate_url_for_ssrf(cls, url: str) -> None:
        """Enforces SSRF prevention checks against external URLs."""
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            raise MediaValidationError(f"Invalid URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

        hostname = parsed.hostname
        if not hostname:
            raise MediaValidationError("URL must include a valid hostname.")

        # Disallow explicit localhost names
        if hostname.lower() in ("localhost", "127.0.0.1", "metadata.google.internal", "instance-data"):
            raise MediaValidationError(f"Access to host '{hostname}' is blocked by SSRF security policy.")

        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                for net in cls.BLOCKED_IP_NETWORKS:
                    if ip_obj in net:
                        raise MediaValidationError(
                            f"Host '{hostname}' resolves to private/reserved IP {ip_str}, blocked by SSRF policy."
                        )
        except socket.gaierror:
            # If resolution fails, let HTTP client handle connection failure or re-raise
            pass

    @classmethod
    async def ingest_from_url(cls, url: str) -> str:
        """Downloads media from URL safely with SSRF protection, size limits, and timeout."""
        cls.validate_url_for_ssrf(url)
        target_file = settings.STORAGE_DIR / f"download_{uuid.uuid4().hex[:8]}.mp4"

        try:
            async with httpx.AsyncClient(timeout=settings.DOWNLOAD_TIMEOUT_SECONDS, follow_redirects=True) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        raise MediaValidationError(f"Failed to fetch media from URL. HTTP status: {response.status_code}")

                    # Check Content-Length header
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > settings.MAX_UPLOAD_SIZE_BYTES:
                        raise MediaValidationError(
                            f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes."
                        )

                    total_bytes = 0
                    with open(target_file, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            total_bytes += len(chunk)
                            if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                                raise MediaValidationError("File exceeded maximum allowed download size during stream.")
                            f.write(chunk)

            logger.info("Successfully ingested media from URL: %s (%d bytes)", url, total_bytes)
            return str(target_file)
        except Exception as e:
            if target_file.exists():
                target_file.unlink(missing_ok=True)
            if isinstance(e, MediaValidationError):
                raise
            raise MediaValidationError(f"Failed to download media from URL: {str(e)}")

    @classmethod
    def calculate_sha256(cls, file_path: str) -> str:
        """Calculates SHA-256 hash of a file for Must-Have 1 verification."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @classmethod
    def inspect_and_register(cls, file_path: str) -> SourceMedia:
        """
        Validates container (MP4 / MOV), inspects streams, detects VFR,
        calculates SHA-256 hash, and constructs a SourceMedia model.
        """
        if not os.path.exists(file_path):
            raise MediaValidationError(f"Media file not found: {file_path}")

        ext = Path(file_path).suffix.lower()
        if ext not in (".mp4", ".mov", ".m4v"):
            raise MediaValidationError(f"Unsupported media container '{ext}'. Only MP4 and MOV are supported.")

        info = VideoRenderer.get_media_info(file_path)
        sha256_val = cls.calculate_sha256(file_path)

        media = SourceMedia(
            id=str(uuid.uuid4()),
            uri=os.path.abspath(file_path),
            duration_ms=info["duration_ms"],
            fps=info["fps"],
            width=info["width"],
            height=info["height"],
            audio_channels=info["audio_channels"],
            audio_sample_rate=info["audio_sample_rate"],
            sha256=sha256_val,
        )
        logger.info("Registered source media %s (duration: %.2fs, sha256: %s)", media.id, info["duration_s"], sha256_val[:10])
        return media
