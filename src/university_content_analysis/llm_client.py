"""OpenAI client abstraction."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI


class MissingAPIKeyError(RuntimeError):
    """Raised when an OpenAI API key is unavailable."""


class LLMRequestError(RuntimeError):
    """Raised when a language-model request fails."""


@dataclass(slots=True)
class OpenAIClient:
    """Small wrapper around the OpenAI Responses API."""

    model: str = "gpt-5.4-mini"
    api_key: str | None = None
    temperature: float = 0.0
    _client: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        resolved_key = self.api_key or os.getenv("OPENAI_API_KEY")

        if not resolved_key:
            raise MissingAPIKeyError(
                "OPENAI_API_KEY is not configured. Export the key before "
                "running classification."
            )

        self._client = OpenAI(api_key=resolved_key)

    def generate(
        self,
        prompt: str,
        system_prompt: str = (
            "You are a strict multi-label classifier. Return JSON only."
        ),
    ) -> str:
        """Send a prompt and return the model's text response."""

        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        try:
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=self.temperature,
            )
        except Exception as exc:
            raise LLMRequestError(f"Language-model request failed: {exc}") from exc

        output_text = response.output_text

        if not output_text or not output_text.strip():
            raise LLMRequestError("The model returned an empty response.")

        return output_text.strip()
