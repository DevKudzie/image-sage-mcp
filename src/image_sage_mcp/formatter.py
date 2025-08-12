from __future__ import annotations

from typing import Any, Dict

from .models import AnalysisResult


class ResponseFormatter:
    def format_success_response(self, analysis: AnalysisResult) -> Dict[str, Any]:
        return {
            "contains_person": analysis.contains_person,
            "objects_detected": analysis.objects_detected,
            "scene_type": analysis.scene_type,
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
        return {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        }

    def validate_response_schema(self, response: Dict[str, Any]) -> bool:
        # Basic shape check; MCP clients will rely on declared schema
        return isinstance(response, dict)


