# Caching

Caching prevents redundant API calls by storing responses and returning them when the same request is made again. This saves time and money during development.

## How It Works

Sutram generates a cache key from the **model name** and the **full message list**. If a matching key is found in the cache, the stored `LLMResponse` is deserialized and returned without making an API call. Cache values are stored as JSON strings.

## Using DictCache

`DictCache` is a simple in-memory cache included with Sutram:

```python
from sutram import create_provider, DictCache

cache = DictCache()
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
    cache=cache,
)

# Hits the API
response = provider.call_llm("Hello!")

# Returns cached result instantly
response = provider.call_llm("Hello!")
```

!!! note
    `DictCache` is in-memory only. Cached responses are lost when your program exits.

## Building a Custom Cache

Any object that implements `get` and `set` methods can be used as a cache. Here's an example using a JSON file for persistence:

```python
import json
from pathlib import Path

class FileCache:
    def __init__(self, path: str = ".llm_cache.json"):
        self.path = Path(path)
        self._store = {}
        if self.path.exists():
            self._store = json.loads(self.path.read_text())

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value
        self.path.write_text(json.dumps(self._store))
```

Use it the same way:

```python
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
    cache=FileCache(),
)
```

## Cache Protocol

To create a compatible cache backend, implement the `Cache` protocol:

```python
from sutram import Cache

class MyCache:
    def get(self, key: str) -> str | None:
        """Return cached value or None if not found."""
        ...

    def set(self, key: str, value: str) -> None:
        """Store a value in the cache."""
        ...
```

## Disabling Cache

Simply don't pass a `cache` argument to `create_provider`:

```python
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
    # No cache — every call hits the API
)
```