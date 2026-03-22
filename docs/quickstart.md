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

## What's Next?

- [Providers](providers.md) — Configure providers and build your own
- [Caching](caching.md) — Explore caching strategies
- [Sessions](sessions.md) — Advanced session management
- [Retry Policies](retry.md) — Handle API failures