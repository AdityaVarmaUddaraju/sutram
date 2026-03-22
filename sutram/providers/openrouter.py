"""OpenRouter API provider."""

import logging

from ..base import BaseProvider
from ..registry import register_provider
from ..response import LLMResponse, Usage, ToolCall

logger = logging.getLogger(__name__)

@register_provider("openrouter", base_url="https://openrouter.ai/api/v1/chat/completions")
class OpenRouterProvider(BaseProvider):
    def _build_request_body(self, messages: list[dict]) -> dict:
        return {"model": self.model, "messages": messages}

    def _parse_response(self, data: dict) -> LLMResponse:
        choice = data["choices"][0]
        message = choice["message"]
        tool_calls = [
            ToolCall(
                id=tc["id"],
                type=tc.get("type", "function"),
                function_name=tc["function"]["name"],
                function_arguments=tc["function"]["arguments"],
            )
            for tc in message.get("tool_calls", [])
        ]
        usage_data = data.get("usage", {})
        return LLMResponse(
            content=message.get("content"),
            reasoning=message.get("reasoning"),
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason"),
            usage=Usage(**usage_data),
            raw=data,
        )
