"""OpenRouter API provider."""

from ..registry import register_provider
from .openai_compat import OpenAICompatProvider


@register_provider("openrouter", base_url="https://openrouter.ai/api/v1/chat/completions")
class OpenRouterProvider(OpenAICompatProvider):
    pass
