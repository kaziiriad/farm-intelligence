"""Tree analysis client — proxies image upload to WeatherAI tree analysis endpoint."""
from typing import Any

import httpx


class TreeAnalysisError(Exception):
    """Raised when tree analysis fails."""


class TreeAnalysisClient:
    """Analyzes tree images via WeatherAI tree analysis endpoint."""

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
        """Send image to WeatherAI tree analysis endpoint, return parsed result."""
        try:
            response = await self._http.post(
                f"{self._base_url}/v1/trees/analyze",
                files={"image": ("tree.jpg", image_data, mime_type)},
                timeout=30.0,
            )

            if response.status_code != 200:
                raise TreeAnalysisError(
                    f"WeatherAI tree analysis returned {response.status_code}: {response.text}"
                )

            return response.json()

        except httpx.HTTPStatusError as exc:
            raise TreeAnalysisError(
                f"HTTP error during tree analysis: {exc}"
            ) from exc
        except Exception as exc:
            raise TreeAnalysisError(f"Tree analysis failed: {exc}") from exc