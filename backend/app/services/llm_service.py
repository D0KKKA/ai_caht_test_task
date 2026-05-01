"""LLM service for OpenRouter API integration."""

import json
import httpx
from typing import AsyncGenerator
from functools import lru_cache

from app.core.config import get_settings
from app.core.constants import (
    LLM_HTTP_REFERER,
    LLM_APP_TITLE,
    SSE_DATA_PREFIX,
    SSE_DATA_OFFSET,
    SSE_DONE_SENTINEL,
)


class LLMService:
    """Service for interacting with OpenRouter API."""

    def __init__(self):
        """Initialize LLM service with settings."""
        self.settings = get_settings()
        self.api_key = self.settings.openrouter_api_key
        self.api_url = self.settings.openrouter_api_url
        self.model = self.settings.model_name
        self.timeout = self.settings.llm_request_timeout
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Create or reuse a single AsyncClient with keep-alive connections."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                ),
            )
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """Build standard OpenRouter headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": LLM_HTTP_REFERER,
            "X-Title": LLM_APP_TITLE,
        }

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def stream_completion(
        self, messages: list[dict], temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Stream completion from OpenRouter, yielding content chunks.

        Args:
            messages: List of message dicts with role and content keys
            temperature: Sampling temperature (0.0-1.0)

        Yields:
            Content chunks as strings
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
        }

        yielded_content = False
        try:
            async with self._get_client().stream(
                "POST",
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_text = (await response.aread()).decode()
                    raise RuntimeError(
                        f"OpenRouter API error {response.status_code}: {error_text}"
                    )

                async for line in response.aiter_lines():
                    if not line.startswith(SSE_DATA_PREFIX):
                        continue

                    data = line[SSE_DATA_OFFSET:]
                    if data == SSE_DONE_SENTINEL:
                        break

                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yielded_content = True
                        yield content
        except httpx.HTTPError as e:
            state = "after streaming started" if yielded_content else "before streaming started"
            raise RuntimeError(f"OpenRouter streaming failed {state}: {e}") from e

    async def completion(
        self, messages: list[dict], temperature: float = 0.7
    ) -> str:
        """Get a non-streaming completion from OpenRouter.

        Args:
            messages: List of message dicts with role and content keys
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Full response text

        Raises:
            Exception: If API call fails
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
        }

        try:
            response = await self._get_client().post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
        except httpx.HTTPError as e:
            raise RuntimeError(f"OpenRouter completion failed: {e}") from e

        if response.status_code != 200:
            raise RuntimeError(
                f"OpenRouter API error {response.status_code}: {response.text}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    """Get cached LLM service instance (singleton)."""
    return LLMService()


async def close_llm_service() -> None:
    """Close the cached LLM service client."""
    await get_llm_service().close()
