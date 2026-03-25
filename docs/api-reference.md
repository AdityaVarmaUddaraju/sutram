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
    verify: bool | str = True,
) -> BaseProvider
```

Creates and returns a configured provider instance.

---

## Response Models

### `LLMResponse`

The unified response object returned by all provider methods.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | `str \| None` | `None` | Text content of the response |
| `reasoning` | `str \| None` | `None` | Model reasoning/thinking content, if present |
| `tool_calls` | `list[ToolCall]` | `[]` | Tool/function calls requested by the model |
| `finish_reason` | `str \| None` | `None` | Why the model stopped (`"stop"`, `"length"`, `"tool_calls"`, etc.) |
| `usage` | `Usage` | `Usage()` | Token usage statistics |
| `raw` | `dict` | `{}` | Full raw response from the provider API |
| `parsed` | `Any` | `None` | Validated Pydantic model instance when using `ResponseSchema` |

`LLMResponse` provides a rich HTML representation in notebooks with collapsible sections for reasoning, tool calls, and raw response data.

### `Usage`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt_tokens` | `int` | `0` | Tokens in the prompt |
| `completion_tokens` | `int` | `0` | Tokens in the completion |
| `total_tokens` | `int` | `0` | Total tokens used |

### `ToolCall`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `str` | required | Unique tool call ID |
| `type` | `str` | `"function"` | Tool call type |
| `function_name` | `str` | required | Name of the function to call |
| `function_arguments` | `str` | required | JSON string of function arguments |

### `StreamDelta`

A single chunk from a streaming response.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | `str \| None` | `None` | Text fragment for this chunk |
| `finish_reason` | `str \| None` | `None` | Set on the final chunk (e.g. `"stop"`) |
| `usage` | `Usage \| None` | `None` | Token usage, if provided on the final chunk |

---

## BaseProvider

The base class for all providers. Handles caching, retries, and both sync/async requests.

### Methods

#### `call_llm`

```python
call_llm(prompt: str, system_prompt: str | None = None, response_schema: ResponseSchema | None = None, tool_config: ToolConfig | None = None) -> LLMResponse
```

Single-turn synchronous call. Optionally include a system prompt, a `ResponseSchema` for structured output, and a `ToolConfig` for tool calling.

#### `acall_llm`

```python
async acall_llm(prompt: str, system_prompt: str | None = None, response_schema: ResponseSchema | None = None, tool_config: ToolConfig | None = None) -> LLMResponse
```

Async version of `call_llm`.

#### `chat`

```python
chat(messages: list[dict], response_schema: ResponseSchema | None = None, tool_config: ToolConfig | None = None) -> LLMResponse
```

Multi-turn synchronous call. Pass a full message list (e.g. from `Session.get_messages()`).

#### `achat`

```python
async achat(messages: list[dict], response_schema: ResponseSchema | None = None, tool_config: ToolConfig | None = None) -> LLMResponse
```

Async version of `chat`.

#### `stream_llm`

```python
stream_llm(prompt: str, system_prompt: str | None = None, tool_config: ToolConfig | None = None) -> Generator[StreamDelta, None, None]
```

Single-turn synchronous streaming call. Yields `StreamDelta` objects as tokens arrive.

#### `astream_llm`

```python
async astream_llm(prompt: str, system_prompt: str | None = None, tool_config: ToolConfig | None = None) -> AsyncGenerator[StreamDelta, None]
```

Async version of `stream_llm`.

#### `stream_chat`

```python
stream_chat(messages: list[dict], tool_config: ToolConfig | None = None) -> Generator[StreamDelta, None, None]
```

Multi-turn synchronous streaming call. Pass a full message list (e.g. from `Session.get_messages()`).

#### `astream_chat`

```python
async astream_chat(messages: list[dict], tool_config: ToolConfig | None = None) -> AsyncGenerator[StreamDelta, None]
```

Async version of `stream_chat`.

!!! note
    Streaming methods do not support `response_schema`. Use the non-streaming methods for structured output.

### Subclassing

Implement these methods to create a custom provider:

```python
def _build_request_body(self, messages: list[dict], response_format: dict | None = None) -> dict
def _parse_response(self, data: dict) -> LLMResponse
def _parse_stream_chunk(self, data: dict) -> StreamDelta  # required for streaming support
```

If the provider uses the OpenAI chat completions format, extend `OpenAICompatProvider` instead (see below).

---

## OpenAICompatProvider

```python
class OpenAICompatProvider(BaseProvider)
```

Base class for providers that use the OpenAI chat completions request/response format. Implements `_build_request_body` and `_parse_response` so subclasses typically need no additional code.

**Handles automatically:**

- Standard `{"model": ..., "messages": ...}` request body
- Response parsing for `content`, `reasoning`, `tool_calls`, `finish_reason`, and `usage`
- Stream chunk parsing for `content`, `finish_reason`, and `usage`

**Usage:**

```python
from sutram import OpenAICompatProvider, register_provider

@register_provider("openai", base_url="https://api.openai.com/v1/chat/completions")
class OpenAIProvider(OpenAICompatProvider):
    pass
```

Subclasses can override `_build_request_body` or `_parse_response` if the provider has minor differences from the standard format.

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

### `ToolConfig`

Configuration for tool calling.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tools` | `list[dict]` | required | List of OpenAI-compatible tool definitions |
| `tool_choice` | `str \| dict \| None` | `None` | Tool choice strategy: `None`/omitted (auto), `"required"`, `"none"`, or a dict to force a specific tool |

### `ResponseSchema`

Configuration for structured output with automatic validation and retry.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `response_model` | `type[BaseModel]` | required | Pydantic model class to validate the response against |
| `max_parse_retries` | `int` | `3` | Maximum number of retry attempts if the response fails validation |

When passed to `call_llm`, `chat`, `acall_llm`, or `achat`, the provider will:

1. Convert the Pydantic model to a JSON schema and include it in `response_format`
2. Validate the response content against the model
3. If validation fails, send the error back to the LLM and retry up to `max_parse_retries` times
4. Attach the validated instance to `response.parsed`

### `RequestConfig`

| Field | Type | Description |
|-------|------|-------------|
| `api_config` | `APIConfig` | API configuration |
| `sync_client` | `httpx.Client \| None` | Optional shared sync HTTP client |
| `async_client` | `httpx.AsyncClient \| None` | Optional shared async HTTP client |
| `verify` | `bool \| str` | SSL verification: `True` (default), `False` to disable, or path to a CA bundle `.pem` file |

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

---

## Tool Utilities

### `@tool`

```python
@tool
def my_function(param: str, optional_param: int = 5):
    """Description of the function"""
    ...
```

Decorator that attaches an OpenAI-compatible tool schema to a function as `my_function.schema`. The function remains callable as normal.

- Parameters **must** have type annotations
- The docstring becomes the tool description
- Parameters with defaults are marked as optional in the schema
- Supported types: `str`, `int`, `float`, `bool`, `list`

### `make_tool_config`

```python
make_tool_config(*funcs, tool_choice: str | dict | None = None) -> ToolConfig
```

Creates a `ToolConfig` from one or more `@tool`-decorated functions.

```python
from sutram import tool, make_tool_config

@tool
def get_weather(location: str):
    """Get the current weather for a location"""
    ...

@tool
def search_restaurants(city: str, cuisine: str = "any"):
    """Search for restaurants in a city"""
    ...

tc = make_tool_config(get_weather, search_restaurants)
result = provider.call_llm("...", tool_config=tc)
```