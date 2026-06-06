"""Tree analysis client — calls AI vision API to analyze tree health from images."""
import base64
import json
from typing import Any

import httpx

from app.core.config import get_settings


class TreeAnalysisError(Exception):
    """Raised when tree analysis fails."""


class TreeAnalysisClient:
    """Analyzes tree images via OpenAI Vision API."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        cache: Any,
        base_url: str,
        api_key: str,
    ) -> None:
        self._http = http_client
        self._cache = cache
        self._base_url = base_url
        self._api_key = api_key

    async def analyze_tree_image(self, image_data: bytes, mime_type: str) -> dict[str, Any]:
        """Send image to OpenAI Vision, return parsed JSON result."""
        b64_image = base64.b64encode(image_data).decode("utf-8")

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "You are an agricultural expert analyzing tea crop health from images. "
                        "Return a JSON object with fields: "
                        "health_status (one of: healthy, stressed, diseased), "
                        "confidence (float 0-1), "
                        "issues (array of strings describing problems seen), "
                        "recommendation (string with actionable advice). "
                        "Only respond with valid JSON, no markdown or explanation."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}",
                            },
                        },
                    ],
                },
            ],
            "max_tokens": 500,
        }

        try:
            response = await self._http.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                raise TreeAnalysisError(f"OpenAI API returned {response.status_code}: {response.text}")

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse JSON from response content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                raise TreeAnalysisError(f"Non-JSON response from OpenAI: {content[:200]}")

        except httpx.HTTPStatusError as exc:
            raise TreeAnalysisError(f"HTTP error during tree analysis: {exc}") from exc
        except Exception as exc:
            raise TreeAnalysisError(f"Tree analysis failed: {exc}") from exc