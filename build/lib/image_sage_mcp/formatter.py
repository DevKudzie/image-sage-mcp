from __future__ import annotations

from typing import Any, Dict

from .models import AnalysisResult


class ResponseFormatter:
    def format_success_response(self, analysis: AnalysisResult) -> Dict[str, Any]:
        return {
            "contains_person": analysis.contains_person,
            "objects_detected": analysis.objects_detected,
            "scene_type": analysis.scene_type,
            "description": analysis.description,
            "ocr_text": analysis.ocr_text,
            "confidence": analysis.confidence,
            "metadata": {
                "width": analysis.metadata.width,
                "height": analysis.metadata.height,
                "mime_type": analysis.metadata.mime_type,
                "file_size_bytes": analysis.metadata.file_size_bytes,
                "format": analysis.metadata.format,
            },
            "processing_time_ms": analysis.processing_time_ms,
            "backend_used": analysis.backend_used,
        }

    def format_error_response(self, code: str, message: str, details: Dict[str, Any] | None = None) -> Dict[str, Any]:
        tips: Dict[str, Any] = {}
        url = (details or {}).get("url") if isinstance(details, dict) else None
        if code in {"INVALID_URL", "FETCH_ERROR"} and isinstance(url, str):
            if url.lower().startswith("file://") or ":\\" in url or url.startswith("/"):
                tips["try_file_url"] = "Use a file:// URL with forward slashes, e.g. file:///C:/path/to/image.jpg"
                tips["allow_fs_root_env"] = "Set IMAGE_SAGE_ALLOWED_FS_ROOTS to include the folder, e.g. C:\\Users\\You\\Desktop"
            else:
                tips["http_https_only"] = "Ensure the URL uses http or https and is publicly reachable (no private IPs)."
        if code == "FETCH_ERROR":
            tips["size_limit_mb"] = "Image may exceed size limit. Adjust IMAGE_SAGE_MAX_MB if needed."
        if code == "PROCESSING_ERROR":
            tips["try_model"] = "Try a different OPENROUTER_MODEL if the provider rejects data URLs."
        return {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "tips": tips,
            }
        }

    def validate_response_schema(self, response: Dict[str, Any]) -> bool:
        # Basic shape check; MCP clients will rely on declared schema
        return isinstance(response, dict)


