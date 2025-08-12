from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
import base64
import json
import httpx

from .models import AnalysisResult, ImageData, ImageMetadata


class VisionBackend:
    name: str = "stub"

    async def analyze(self, image: ImageData, options: Optional[Dict[str, Any]] = None) -> Optional[AnalysisResult]:
        raise NotImplementedError


class StubBackend(VisionBackend):
    name = "stub"

    async def analyze(self, image: ImageData, options: Optional[Dict[str, Any]] = None) -> Optional[AnalysisResult]:
        start = time.perf_counter()
        # Very naive heuristic placeholder
        contains_person = False
        objects_detected: List[str] = []
        scene_type = "unknown"
        description = ""
        ocr_text = ""
        confidence = 0.25
        meta = ImageMetadata(
            width=image.width or 0,
            height=image.height or 0,
            mime_type=image.mime_type,
            file_size_bytes=image.file_size_bytes,
            format=image.format,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return AnalysisResult(
            contains_person=contains_person,
            objects_detected=objects_detected,
            scene_type=scene_type,
            description=description,
            ocr_text=ocr_text,
            confidence=confidence,
            metadata=meta,
            processing_time_ms=elapsed_ms,
            backend_used=self.name,
        )


class VisionProcessor:
    def __init__(self, backends: List[VisionBackend]) -> None:
        self.backends = backends

    async def analyze_image(self, image_data: ImageData, options: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        last_error: Optional[Exception] = None
        for backend in self.backends:
            try:
                result = await backend.analyze(image_data, options)
                if result is not None:
                    return result
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
        if last_error:
            raise last_error
        raise RuntimeError("All vision backends returned no result")


class OpenRouterBackend(VisionBackend):
    name = "openrouter"

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 20) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def analyze(self, image: ImageData, options: Optional[Dict[str, Any]] = None) -> Optional[AnalysisResult]:
        # Prepare base64 data URL
        b64 = base64.b64encode(image.bytes_data).decode("ascii")
        data_uri = f"data:{image.mime_type};base64,{b64}"

        include_ocr = True
        detail_level = "medium"
        if isinstance(options, dict):
            include_ocr = bool(options.get("include_ocr", True))
            detail_level = str(options.get("detail_level", "medium"))

        system_prompt = (
            "You are an image analysis engine. Return only a compact JSON object with keys: "
            "contains_person (bool), objects_detected (array of strings), scene_type (string), "
            "description (string, a concise natural language summary), ocr_text (string), confidence (0..1)."
        )
        user_prompt = (
            f"Analyze the image with {detail_level} detail. "
            + ("Include OCR text in 'ocr_text'. " if include_ocr else "Set 'ocr_text' to an empty string. ")
            + "Do not include any text outside of the JSON object."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://local.image-sage-mcp",
            "X-Title": "Image Sage MCP",
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds, base_url="https://openrouter.ai/api/v1") as client:
            resp = await client.post("/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Extract the first choice content
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"OpenRouter malformed response: {exc}")

        try:
            parsed = json.loads(content)
        except Exception:
            # If not strict JSON, try to heuristically extract
            # Fallback to minimal structure
            parsed = {}

        contains_person = bool(parsed.get("contains_person", False))
        objects_detected = list(parsed.get("objects_detected", []))
        scene_type = str(parsed.get("scene_type", "unknown"))
        description = str(parsed.get("description", ""))
        ocr_text = str(parsed.get("ocr_text", ""))
        confidence = float(parsed.get("confidence", 0.5))

        meta = ImageMetadata(
            width=image.width or 0,
            height=image.height or 0,
            mime_type=image.mime_type,
            file_size_bytes=image.file_size_bytes,
            format=image.format,
        )

        # processing_time_ms is not measured here; leave as 0 (server measures overall)
        return AnalysisResult(
            contains_person=contains_person,
            objects_detected=objects_detected,
            scene_type=scene_type,
            description=description,
            ocr_text=ocr_text,
            confidence=confidence,
            metadata=meta,
            processing_time_ms=0,
            backend_used=self.name,
        )


