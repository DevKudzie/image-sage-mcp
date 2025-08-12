from __future__ import annotations

import io
import os
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx
from PIL import Image

from .models import ImageData


SUPPORTED_FORMATS = {"JPEG", "PNG", "GIF", "WEBP"}
SUPPORTED_MIME = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/gif": "GIF",
    "image/webp": "WEBP",
}


class ImageFetcher:
    def __init__(self, timeout_seconds: int, max_size_mb: int) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_size_bytes = max_size_mb * 1024 * 1024

    async def fetch_from_url(self, url: str) -> ImageData:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            data = response.content
            if len(data) > self.max_size_bytes:
                raise ValueError("Image too large")
            mime_type = response.headers.get("content-type", "").split(";")[0].strip()
            return self._to_imagedata(data, mime_type=mime_type)

    async def fetch_from_file(self, path: str) -> ImageData:
        with open(path, "rb") as f:
            data = f.read()
        if len(data) > self.max_size_bytes:
            raise ValueError("Image too large")
        return self._to_imagedata(data, mime_type=None)

    def _to_imagedata(self, data: bytes, mime_type: Optional[str]) -> ImageData:
        image = Image.open(io.BytesIO(data))
        image_format = (image.format or "").upper()
        if image_format not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported image format: {image_format}")
        width, height = image.size
        if not mime_type:
            # Infer mime
            for k, v in SUPPORTED_MIME.items():
                if v == image_format:
                    mime_type = k
                    break
        return ImageData(
            bytes_data=data,
            mime_type=mime_type or "application/octet-stream",
            format=image_format,
            file_size_bytes=len(data),
            width=width,
            height=height,
        )


