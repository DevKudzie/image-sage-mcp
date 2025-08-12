from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ImageMetadata:
    width: int
    height: int
    mime_type: str
    file_size_bytes: int
    format: str


@dataclass
class AnalysisResult:
    contains_person: bool
    objects_detected: List[str]
    scene_type: str
    description: str
    ocr_text: str
    confidence: float
    metadata: ImageMetadata
    processing_time_ms: int
    backend_used: str


@dataclass
class ServerConfig:
    vision_backends: List[str]
    api_keys: Dict[str, str]
    max_image_size_mb: int = 10
    request_timeout_seconds: int = 10
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    log_level: str = "INFO"
    openrouter_model: str = "openai/gpt-4o-mini"
    allowed_fs_roots: List[str] = None  # set at load time


@dataclass
class ImageData:
    bytes_data: bytes
    mime_type: str
    format: str
    file_size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None


