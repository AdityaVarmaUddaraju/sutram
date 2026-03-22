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

## Creating a Custom Provider

Use the `@register_provider` decorator to register your provider:

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

## Sync vs Async

Every provider supports both sync and async methods:

| Sync | Async | Description |
|------|-------|-------------|
| `call_llm(prompt)` | `acall_llm(prompt)` | Single-turn call |
| `chat(messages)` | `achat(messages)` | Multi-turn with message list |

```python
# Sync
response = provider.call_llm("Hello!")
print(response.content)

# Async
response = await provider.acall_llm("Hello!")
print(response.content)
```