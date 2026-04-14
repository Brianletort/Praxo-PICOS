from __future__ import annotations

import base64
import enum
import logging
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class ModelTier(enum.StrEnum):
    VISION = "vision"
    REASONING = "reasoning"
    LIGHTWEIGHT = "lightweight"


_DEFAULT_MODELS: dict[ModelTier, str] = {
    ModelTier.VISION: "gpt-5.4-pro",
    ModelTier.REASONING: "gpt-5.4",
    ModelTier.LIGHTWEIGHT: "gpt-5.4-mini",
}


@dataclass
class UsageStats:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    requests: int = 0

    def record(self, prompt: int, completion: int) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += prompt + completion
        self.requests += 1


class LLMProvider:
    """Unified LLM access with tiered model selection.

    Three tiers:
        vision     -- gpt-5.4-pro for frame/image analysis
        reasoning  -- gpt-5.4 for coaching reports, synthesis
        lightweight -- gpt-5.4-mini for headlines, classification, fast tasks
    """

    def __init__(
        self,
        api_key: str | None = None,
        models: dict[ModelTier, str] | None = None,
        base_url: str | None = None,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._models = {**_DEFAULT_MODELS, **(models or {})}
        self._usage: dict[ModelTier, UsageStats] = {
            tier: UsageStats() for tier in ModelTier
        }

    def model_for(self, tier: ModelTier) -> str:
        return self._models[tier]

    @property
    def usage(self) -> dict[str, Any]:
        return {tier.value: {"tokens": s.total_tokens, "requests": s.requests}
                for tier, s in self._usage.items()}

    async def complete_text(
        self,
        prompt: str,
        *,
        tier: ModelTier = ModelTier.LIGHTWEIGHT,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """Text completion using the specified model tier."""
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self._models[tier],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._track_usage(tier, response)
        return response.choices[0].message.content or ""

    async def complete_structured(
        self,
        prompt: str,
        *,
        tier: ModelTier = ModelTier.LIGHTWEIGHT,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """JSON-mode completion returning a parsed dict."""
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self._models[tier],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        self._track_usage(tier, response)
        import json
        raw = response.choices[0].message.content or "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse structured response as JSON")
            return {"raw": raw}

    async def complete_vision(
        self,
        prompt: str,
        image_data: bytes | str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        detail: str = "high",
    ) -> dict[str, Any]:
        """Vision analysis on a single image. Always uses the vision tier model.

        image_data: raw bytes or base64-encoded string.
        """
        if isinstance(image_data, bytes):
            b64 = base64.b64encode(image_data).decode("utf-8")
        else:
            b64 = image_data

        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}", "detail": detail},
                },
            ],
        })

        response = await self._client.chat.completions.create(
            model=self._models[ModelTier.VISION],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        self._track_usage(ModelTier.VISION, response)
        import json
        raw = response.choices[0].message.content or "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}

    def _track_usage(self, tier: ModelTier, response: Any) -> None:
        if hasattr(response, "usage") and response.usage:
            self._usage[tier].record(
                response.usage.prompt_tokens or 0,
                response.usage.completion_tokens or 0,
            )
