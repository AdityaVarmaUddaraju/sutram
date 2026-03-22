"""Base provider for OpenAI-compatible APIs."""

from ..base import BaseProvider
from ..response import LLMResponse, Usage, ToolCall


class OpenAICompatProvider(BaseProvider):
    """Base class for providers using the OpenAI chat completions format."""

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
