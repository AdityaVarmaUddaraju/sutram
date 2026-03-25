# Quick Start

This guide will get you up and running with Sutram in 5 minutes.

## Prerequisites

- Python 3.11+
- An API key from a supported provider (e.g. [OpenRouter](https://openrouter.ai))

## Installation

```bash
pip install sutram
```

## Setting Up Your API Key

We recommend storing your API key in an environment variable rather than hardcoding it:

```bash
export OPEN_ROUTER_API_KEY="your-api-key-here"
```

Or use a `.env` file with `python-dotenv`:

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()
```

## Your First Call

```python
import os
from sutram import create_provider

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
)

response = provider.call_llm("Hello, world!")
print(response.content)
```

## Adding Caching

Avoid repeated API calls by adding a cache:

```python
from sutram import create_provider, DictCache

cache = DictCache()
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
    cache=cache,
)

# First call hits the API
response = provider.call_llm("Hello!")

# Second identical call returns from cache (same LLMResponse)
response = provider.call_llm("Hello!")
```

## Multi-turn Conversation

```python
from sutram import create_provider, Session

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
)

session = Session(system_prompt="You are a helpful assistant.")
session.add_user_message("What is Python?")

response = provider.chat(session.get_messages())
print(response.content)

session.add_assistant_message(response.content)
session.add_user_message("What are its main features?")

response = provider.chat(session.get_messages())
print(response.content)
```

## Async Support

```python
import asyncio
from sutram import create_provider

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
)

async def main():
    response = await provider.acall_llm("Hello from async!")
    print(response.content)

asyncio.run(main())
```

## Streaming

Stream responses token-by-token for a better user experience:

```python
from sutram import create_provider

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
)

# Sync streaming
for delta in provider.stream_llm("Tell me a short story"):
    if delta.content:
        print(delta.content, end="", flush=True)
print()
```

Async streaming works the same way:

```python
async for delta in provider.astream_llm("Tell me a short story"):
    if delta.content:
        print(delta.content, end="", flush=True)
print()
```

You can also stream multi-turn conversations with `stream_chat`:

```python
from sutram import Session

session = Session(system_prompt="You are a helpful assistant.")
session.add_user_message("What is Python?")

for delta in provider.stream_chat(session.get_messages()):
    if delta.content:
        print(delta.content, end="", flush=True)
print()
```

!!! note
    Streamed responses are automatically cached after completion. Subsequent identical calls return the full response instantly from cache.

## Tool Calling

Define tools using the `@tool` decorator and let the LLM call them:

```python
from sutram import create_provider, tool, make_tool_config

@tool
def get_weather(location: str, units: str = "celsius"):
    """Get the current weather for a location"""
    return f"Sunny, 25° in {location}"

@tool
def search_restaurants(city: str, cuisine: str = "any"):
    """Search for restaurants in a city by cuisine type"""
    return f"Found restaurants in {city}"

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
)

tc = make_tool_config(get_weather, search_restaurants)
result = provider.call_llm("What's the weather in Tokyo?", tool_config=tc)
print(result.tool_calls)  # LLM requests to call get_weather
```

You can control tool selection with `tool_choice`:

```python
# Force the model to call a tool
tc = make_tool_config(get_weather, tool_choice="required")

# Force a specific tool
tc = make_tool_config(get_weather, search_restaurants, tool_choice={
    "type": "function", "function": {"name": "get_weather"}
})
```

## Structured Output

Get validated, typed responses using Pydantic models:

```python
from pydantic import BaseModel, Field
from sutram import create_provider, ResponseSchema

class Person(BaseModel):
    name: str
    age: int = Field(ge=0, le=150)

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
)

schema = ResponseSchema(response_model=Person)
result = provider.call_llm("Invent a person with a name and age.", response_schema=schema)

print(result.parsed)       # Person(name='Alex Rivera', age=28)
print(result.parsed.name)  # 'Alex Rivera'
print(result.content)      # Raw JSON string from the LLM
```

If the LLM returns invalid JSON or fails Pydantic validation, the error is automatically sent back to the LLM for correction, up to `max_parse_retries` times (default: 3).

## SSL Verification

By default, Sutram verifies SSL certificates using your system's trusted CA bundle. You can customize this behavior with the `verify` parameter:

```python
# Disable SSL verification (not recommended for production)
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
    verify=False,
)

# Use a custom CA bundle (e.g. for corporate proxies)
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
    verify="/path/to/ca-bundle.pem",
)
```

## What's Next?

- [Providers](providers.md) — Configure providers and build your own
- [Caching](caching.md) — Explore caching strategies
- [Sessions](sessions.md) — Advanced session management
- [Retry Policies](retry.md) — Handle API failures