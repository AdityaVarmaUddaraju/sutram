# sūtram (సూత్రం)

*The thread that connects your code to any language model.*

Sutram is a lightweight Python library that provides a unified interface for calling LLMs — with built-in caching, retry policies, and multi-turn session management.

## Why Sutram?

- **One interface, many providers** — Switch between OpenRouter, OpenAI, Anthropic, and more without changing your code
- **Built-in caching** — Never pay for the same API call twice
- **Automatic retries** — Handle transient failures with configurable backoff strategies
- **Multi-turn sessions** — Manage conversation history effortlessly
- **Sync & Async** — Full support for both workflows
- **Extensible** — Add custom providers in minutes

## Installation

```bash
pip install sutram
```

## Minimal Example

```python
from sutram import create_provider

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
)

response = provider.call_llm("What is the meaning of sūtram?")
print(response)
```

## Next Steps

- [Quick Start](quickstart.md) — Get up and running in 5 minutes
- [Providers](providers.md) — Configure and create custom providers
- [Caching](caching.md) — Speed up development with response caching
- [Sessions](sessions.md) — Build multi-turn chat applications
- [Retry Policies](retry.md) — Handle API failures gracefully
- [API Reference](api-reference.md) — Full API documentation
```

