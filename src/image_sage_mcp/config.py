from __future__ import annotations

import os
from typing import Dict, List

from .models import ServerConfig


def load_config() -> ServerConfig:
    vision_backends: List[str] = os.getenv("IMAGE_SAGE_BACKENDS", "openrouter,openai,anthropic").split(",")
    api_keys: Dict[str, str] = {}
    if os.getenv("OPENAI_API_KEY"):
        api_keys["openai"] = os.environ["OPENAI_API_KEY"]
    if os.getenv("ANTHROPIC_API_KEY"):
        api_keys["anthropic"] = os.environ["ANTHROPIC_API_KEY"]
    if os.getenv("OPENROUTER_API_KEY"):
        api_keys["openrouter"] = os.environ["OPENROUTER_API_KEY"]

    max_image_size_mb = int(os.getenv("IMAGE_SAGE_MAX_MB", "10"))
    request_timeout_seconds = int(os.getenv("IMAGE_SAGE_TIMEOUT", "10"))
    cache_enabled = os.getenv("IMAGE_SAGE_CACHE", "1") not in {"0", "false", "False"}
    cache_ttl_seconds = int(os.getenv("IMAGE_SAGE_CACHE_TTL", "3600"))
    log_level = os.getenv("IMAGE_SAGE_LOG", "INFO")

    roots_env = os.getenv("IMAGE_SAGE_ALLOWED_FS_ROOTS", "").strip()
    allowed_fs_roots = [p.strip() for p in roots_env.split(";") if p.strip()] if roots_env else []

    return ServerConfig(
        vision_backends=[b.strip() for b in vision_backends if b.strip()],
        api_keys=api_keys,
        max_image_size_mb=max_image_size_mb,
        request_timeout_seconds=request_timeout_seconds,
        cache_enabled=cache_enabled,
        cache_ttl_seconds=cache_ttl_seconds,
        log_level=log_level,
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        allowed_fs_roots=allowed_fs_roots,
    )


