from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self

import httpx

from backend.app.core.config import settings


class GeminiClientError(RuntimeError):
    """Raised when the Gemini API cannot produce a valid response."""


class GeminiClient:
    """Small asynchronous REST client for Gemini embeddings and generation."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.base_url = (base_url or settings.gemini_api_base_url).rstrip("/")
        self._http_client = http_client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout if timeout is not None else settings.http_timeout,
        )
        self._owns_http_client = http_client is None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_http_client:
            await self._http_client.aclose()

    async def generate_embeddings(self, text: str) -> list[float]:
        response = await self._post(
            "/models/text-embedding-004:embedContent",
            {"content": {"parts": [{"text": text}]}},
        )
        embedding = response.get("embedding", {}).get("values")
        if not isinstance(embedding, list) or not all(
            isinstance(value, (int, float)) for value in embedding
        ):
            raise GeminiClientError("Gemini returned an invalid embedding response")
        return [float(value) for value in embedding]

    async def generate_response(self, prompt: str) -> str:
        response = await self._post(
            "/models/gemini-1.5-flash:generateContent",
            {"contents": [{"parts": [{"text": prompt}]}]},
        )
        try:
            text = response["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GeminiClientError(
                "Gemini returned an invalid generation response"
            ) from exc
        if not isinstance(text, str):
            raise GeminiClientError("Gemini returned an invalid generation response")
        return text

    async def _post(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise GeminiClientError("GEMINI_API_KEY is not configured")

        try:
            response = await self._http_client.post(
                path,
                params={"key": self.api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise GeminiClientError("Gemini API request failed") from exc

        if not isinstance(data, dict):
            raise GeminiClientError("Gemini returned an invalid response")
        return data
