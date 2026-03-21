# API Reference

## Provider Factory

### `create_provider`

```python
create_provider(
    name: str,
    model: str,
    api_key: str | Callable[[], str],
    base_url: str | None = None,
    max_retries: int = 0,
    backoff_factor: float = 1.0,
    strategy: Literal["exponential", "fixed"] = "exponential",
    timeout: int = 120,
    retry_on_status: list[int] | None = None,
    cache: Cache | None = None,
    sync_client: httpx.Client | None = None,
    async_client: httpx.AsyncClient | None = None,
) -> BaseProvider
```

Creates and returns a configured provider instance.

---

## BaseProvider

The base class for all providers. Handles caching, retries, and both sync/async requests.

### Methods

#### `call_llm`

```python
call_llm(prompt: str, system_prompt: str | None = None) -> str
```

Single-turn synchronous call. Optionally include a system prompt.

#### `acall_llm`

```python
async acall_llm(prompt: str, system_prompt: str | None = None) -> str
```

Async version of `call_llm`.

#### `chat`

```python
chat(messages: list[dict]) -> str
```

Multi-turn synchronous call. Pass a full message list (e.g. from `Session.get_messages()`).

#### `achat`

```python
async achat(messages: list[dict]) -> str
```

Async version of `chat`.

### Subclassing

Implement these two methods to create a custom provider:

```python
def _build_request_body(self, messages: list[dict]) -> dict
def _parse_response(self, data: dict) -> str
```

---

## Session

```python
Session(system_prompt: str | None = None)
```

Manages multi-turn conversation history.

### Methods

| Method | Description |
|--------|-------------|
| `add_system_message(content: str)` | Add a system message |
| `add_user_message(content: str)` | Add a user message |
| `add_assistant_message(content: str \| None, tool_calls: list[dict] \| None)` | Add an assistant message |
| `add_tool_message(tool_call_id: str, content: str, name: str \| None)` | Add a tool result message |
| `get_messages() -> list[dict]` | Return a copy of the message list |

---

## Cache

### `Cache` (Protocol)

| Method | Description |
|--------|-------------|
| `get(key: str) -> str \| None` | Return cached value or `None` |
| `set(key: str, value: str) -> None` | Store a value |

### `DictCache`

In-memory cache implementation. No configuration required.

```python
cache = DictCache()
```

---

## Configuration Models

### `RetryPolicy`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_retries` | `int` | `3` | Maximum retry attempts |
| `backoff_factor` | `float` | `1.0` | Base wait time in seconds |
| `strategy` | `"exponential"` \| `"fixed"` | `"exponential"` | Backoff strategy |
| `timeout` | `int` | `120` | Request timeout in seconds |
| `retry_on_status` | `list[int]` | `[429, 500, 502, 503, 504]` | Status codes that trigger retry |

### `APIConfig`

| Field | Type | Description |
|-------|------|-------------|
| `base_url` | `str` | API endpoint URL |
| `api_key` | `str` \| `Callable` | API key or callable that returns one |
| `retry_policy` | `RetryPolicy` | Retry configuration |

### `RequestConfig`

| Field | Type | Description |
|-------|------|-------------|
| `api_config` | `APIConfig` | API configuration |
| `sync_client` | `httpx.Client \| None` | Optional shared sync HTTP client |
| `async_client` | `httpx.AsyncClient \| None` | Optional shared async HTTP client |

---

### `register_provider`

```python
@register_provider(name: str, base_url: str | None = None)
```

Class decorator that registers a `BaseProvider` subclass in the provider registry.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Unique provider name |
| `base_url` | `str \| None` | `None` | Default API endpoint URL |

Add custom providers by using this decorator.