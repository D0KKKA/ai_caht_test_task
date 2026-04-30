"""LLM service for OpenRouter API integration."""

import json
import httpx
from typing import AsyncGenerator
from functools import lru_cache

from app.core.config import get_settings


class LLMService:
    """Service for interacting with OpenRouter API."""

    def __init__(self):
        """Initialize LLM service with settings."""
        self.settings = get_settings()
        self.api_key = self.settings.openrouter_api_key
        self.api_url = self.settings.openrouter_api_url
        self.model = self.settings.model_name

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
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com",
            "X-Title": "AI Chat App",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                self.api_url,
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(
                        f"OpenRouter API error {response.status_code}: {error_text.decode()}"
                    )

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

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
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com",
            "X-Title": "AI Chat App",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                raise Exception(
                    f"OpenRouter API error {response.status_code}: {response.text}"
                )

            data = response.json()
            return data["choices"][0]["message"]["content"]


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    """Get cached LLM service instance (singleton)."""
    return LLMService()
