# Providers

Providers are the bridge between your code and LLM APIs. Sutram ships with OpenRouter support and makes it easy to add your own.

## Using OpenRouter

```python
import os
from sutram import create_provider

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
)

response = provider.call_llm("Hello!")
print(response.content)
```

Any model available on [OpenRouter](https://openrouter.ai/models) can be used by passing its model ID.

## The `create_provider` Function

This is the recommended way to create providers. It handles all the wiring for you:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Provider name (e.g. `"openrouter"`) |
| `model` | `str` | required | Model identifier |
| `api_key` | `str` or `callable` | required | API key or a function that returns one |
| `base_url` | `str` | provider default | Override the API endpoint |
| `max_retries` | `int` | `0` | Number of retry attempts |
| `timeout` | `int` | `120` | Request timeout in seconds |
| `cache` | `Cache` | `None` | Cache backend instance |

## Dynamic API Keys

You can pass a callable instead of a string for the API key. This is useful for key rotation or fetching from a secrets manager:

```python
import os

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=lambda: os.environ["OPEN_ROUTER_API_KEY"],
)
```

## OpenAI-Compatible Providers

Many LLM providers (OpenAI, Groq, Together, Mistral, etc.) use the same request/response format as OpenAI's chat completions API. Sutram provides `OpenAICompatProvider` as a base class for these providers — it handles building the request body and parsing the response (including tool calls, reasoning, and usage) out of the box.

For example, adding OpenAI as a provider is just:

```python
from sutram import OpenAICompatProvider, register_provider

@register_provider("openai", base_url="https://api.openai.com/v1/chat/completions")
class OpenAIProvider(OpenAICompatProvider):
    pass
```

That's it — no need to implement `_build_request_body` or `_parse_response`.

The built-in `OpenRouterProvider` itself extends `OpenAICompatProvider`, so it automatically benefits from full response parsing including tool calls and reasoning content.

## Creating a Custom Provider

If your provider uses the OpenAI format, extend `OpenAICompatProvider` as shown above.

If your provider uses a **different** format, extend `BaseProvider` directly and implement `_build_request_body` and `_parse_response`:

```python
from sutram import BaseProvider, LLMResponse, register_provider

@register_provider("myprovider", base_url="https://api.myprovider.com/v1/chat")
class MyProvider(BaseProvider):
    def _build_request_body(self, messages: list[dict], response_format: dict | None = None, tool_config=None) -> dict:
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

## Sync vs Async

Every provider supports both sync and async methods:

| Sync | Async | Description |
|------|-------|-------------|
| `call_llm(prompt)` | `acall_llm(prompt)` | Single-turn call |
| `chat(messages)` | `achat(messages)` | Multi-turn with message list |
| `stream_llm(prompt)` | `astream_llm(prompt)` | Single-turn streaming |
| `stream_chat(messages)` | `astream_chat(messages)` | Multi-turn streaming |

```python
# Sync
response = provider.call_llm("Hello!")
print(response.content)

# Async
response = await provider.acall_llm("Hello!")
print(response.content)

# Sync streaming
for delta in provider.stream_llm("Hello!"):
    if delta.content:
        print(delta.content, end="", flush=True)

# Async streaming
async for delta in provider.astream_llm("Hello!"):
    if delta.content:
        print(delta.content, end="", flush=True)
```