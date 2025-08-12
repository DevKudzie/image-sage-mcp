from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
import os
import sys

from .config import load_config
from .fetcher import ImageFetcher
from .formatter import ResponseFormatter
from .models import ImageData
from .processor import OpenRouterBackend, StubBackend, VisionProcessor
from .validation import URLValidator


TOOL_SCHEMA: Dict[str, Any] = {
    "name": "Image Sage",
    "description": "Analyze an image from a URL or local file path and return structured information about its contents",
    "inputSchema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL or local file path to the image to analyze"},
            "options": {
                "type": "object",
                "properties": {
                    "include_ocr": {"type": "boolean", "description": "Whether to extract text from the image", "default": True},
                    "detail_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Level of detail for analysis",
                        "default": "medium",
                    },
                },
            },
        },
        "required": ["url"],
    },
}


async def _handle_image_sage(url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config = load_config()

    validator = URLValidator()
    vr = validator.validate_url(url)
    if not vr.ok:
        return ResponseFormatter().format_error_response("INVALID_URL", vr.message or "Invalid URL", {"url": url})

    fetcher = ImageFetcher(timeout_seconds=config.request_timeout_seconds, max_size_mb=config.max_image_size_mb)
    try:
        if url.startswith("http://") or url.startswith("https://"):
            image: ImageData = await fetcher.fetch_from_url(url)
        else:
            # local path or file://
            path = url
            if url.startswith("file://"):
                path = url[len("file://") :]
            image = await fetcher.fetch_from_file(path)
    except Exception as exc:  # noqa: BLE001
        return ResponseFormatter().format_error_response(
            "FETCH_ERROR", "Unable to fetch or read image", {"url": url, "reason": str(exc)}
        )

    backends = []
    if "openrouter" in config.vision_backends and config.api_keys.get("openrouter"):
        backends.append(
            OpenRouterBackend(api_key=config.api_keys["openrouter"], model=config.openrouter_model, timeout_seconds=config.request_timeout_seconds)
        )
    # Always include stub as a final fallback
    backends.append(StubBackend())
    processor = VisionProcessor(backends=backends)
    try:
        analysis = await processor.analyze_image(image, options)
    except Exception as exc:  # noqa: BLE001
        return ResponseFormatter().format_error_response(
            "PROCESSING_ERROR", "Vision processing failed", {"reason": str(exc)}
        )
    return ResponseFormatter().format_success_response(analysis)


def main() -> None:
    # FastMCP-based runner
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore
    except Exception:  # noqa: BLE001
        raise SystemExit(
            "The 'mcp' package is required. Install with: pip install mcp"
        )

    if os.getenv("IMAGE_SAGE_DEBUG", ""):  # basic startup signal to stderr
        sys.stderr.write(f"[image-sage-mcp] starting (pid={os.getpid()})\n")
        sys.stderr.flush()

    mcp = FastMCP("image-sage-mcp")

    @mcp.tool(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
    )
    async def image_sage(url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:  # noqa: D401
        if os.getenv("IMAGE_SAGE_DEBUG", ""):
            sys.stderr.write(f"[image-sage-mcp] tool call: url={url}\n")
            sys.stderr.flush()
        return await _handle_image_sage(url, options)

    mcp.run()


if __name__ == "__main__":
    main()


