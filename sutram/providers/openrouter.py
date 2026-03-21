"""OpenRouter API provider."""

import logging

from ..base import BaseProvider

logger = logging.getLogger(__name__)

class OpenRouterProvider(BaseProvider):
    def _build_request_body(self, messages: list[dict]) -> dict:
        return {"model": self.model, "messages": messages}

    def _parse_response(self, data: dict) -> str:
        return data["choices"][0]["message"]["content"]
