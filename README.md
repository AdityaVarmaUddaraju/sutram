# sūtram (సూత్రం)

*The thread that connects*

A unified Python interface for LLM providers. One thread to connect your code to any language model — with built-in caching, retry policies, and multi-turn session management.

*In Sanskrit, sūtram means "thread" or "formula" — the essential connection that holds everything together.*

## Features

- **Unified Provider Interface** — One API to call OpenRouter, OpenAI, Anthropic, and more
- **Built-in Caching** — Avoid redundant API calls with pluggable cache backends
- **Retry Policies** — Configurable exponential/fixed backoff with status-code filtering
- **Multi-turn Sessions** — First-class support for conversation history management
- **Sync & Async** — Full support for both synchronous and asynchronous workflows
- **Extensible** — Add new providers by subclassing `BaseProvider`

## Installation

```bash
pip install sutram
```

## Quick Start

```python
from sutram import create_provider, Session, DictCache

# Create a provider
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
    cache=DictCache(),
)

# Single-turn call
response = provider.call_llm("What is the meaning of sūtram?")
print(response.content)

# Multi-turn conversation
session = Session(system_prompt="You are a helpful assistant.")
session.add_user_message("Hello!")
response = provider.chat(session.get_messages())
session.add_assistant_message(response.content)
session.add_user_message("Tell me more.")
response = provider.chat(session.get_messages())
```

## Configuration

```python
from sutram import create_provider, DictCache

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
    max_retries=3,
    backoff_factor=1.0,
    strategy="exponential",
    timeout=120,
    retry_on_status=[429, 500, 502, 503, 504],
    cache=DictCache(),
)
```

## Creating a Custom Provider

For providers that use the **OpenAI chat completions format** (OpenAI, Groq, Together, Mistral, etc.), extend `OpenAICompatProvider` — no methods to implement:

```python
from sutram import OpenAICompatProvider, register_provider

@register_provider("openai", base_url="https://api.openai.com/v1/chat/completions")
class OpenAIProvider(OpenAICompatProvider):
    pass
```

For providers with a **different format**, extend `BaseProvider` and implement `_build_request_body` and `_parse_response`:

```python
from sutram import BaseProvider, LLMResponse, register_provider

@register_provider("myprovider", base_url="https://api.myprovider.com/v1/chat")
class MyProvider(BaseProvider):
    def _build_request_body(self, messages: list[dict]) -> dict:
        return {"model": self.model, "messages": messages}

    def _parse_response(self, data: dict) -> LLMResponse:
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            raw=data,
        )
```

Now use it like any built-in provider:

```python
provider = create_provider(
    name="myprovider",
    model="my-model",
    api_key="my-key",
)
```

The `base_url` in the decorator is optional — you can pass it at creation time instead:

```python
@register_provider("myprovider")
class MyProvider(BaseProvider):
    ...

provider = create_provider(
    name="myprovider",
    model="my-model",
    api_key="my-key",
    base_url="https://api.myprovider.com/v1/chat",
)
```


## License

MIT
