"""OpenRouter API provider."""

import logging

from ..base import BaseProvider
from ..registry import register_provider

logger = logging.getLogger(__name__)

@register_provider("openrouter", base_url="https://openrouter.ai/api/v1/chat/completions")
class OpenRouterProvider(BaseProvider):
    def _build_request_body(self, messages: list[dict]) -> dict:
        return {"model": self.model, "messages": messages}

    def _parse_response(self, data: dict) -> str:
        return data["choices"][0]["message"]["content"]
