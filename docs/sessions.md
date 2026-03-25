# Sessions

Sessions manage multi-turn conversation history, making it easy to build chat applications.

## Creating a Session

```python
from sutram import Session

session = Session(system_prompt="You are a helpful assistant.")
```

You can also create a session without a system prompt:

```python
session = Session()
```

## Building a Conversation

Add messages to the session as the conversation progresses:

```python
from sutram import create_provider, Session

provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
)

session = Session(system_prompt="You are a helpful assistant.")

# Turn 1
session.add_user_message("What is Python?")
response = provider.chat(session.get_messages())
print(response.content)
session.add_assistant_message(response.content)

# Turn 2
session.add_user_message("What are its main features?")
response = provider.chat(session.get_messages())
print(response.content)
session.add_assistant_message(response.content)
```

## Message Types

Session supports all standard message roles:

| Method | Role | Description |
|--------|------|-------------|
| `add_system_message(content)` | `system` | System instructions |
| `add_user_message(content)` | `user` | User input |
| `add_assistant_message(content)` | `assistant` | Model response |
| `add_tool_message(tool_call_id, content)` | `tool` | Tool/function result |

## Tool Call Messages

For function-calling workflows:

```python
session.add_user_message("What's the weather in London?")

# Model responds with a tool call
session.add_assistant_message(
    tool_calls=[{
        "id": "call_123",
        "type": "function",
        "function": {"name": "get_weather", "arguments": '{"city": "London"}'}
    }]
)

# Add the tool result
session.add_tool_message(
    tool_call_id="call_123",
    content='{"temp": 15, "condition": "cloudy"}',
    name="get_weather",
)

# Model responds with the final answer
response = provider.chat(session.get_messages())
print(response.content)
```

## Streaming with Sessions

Use `stream_chat` or `astream_chat` to stream responses in a multi-turn conversation:

```python
session = Session(system_prompt="You are a helpful assistant.")
session.add_user_message("Tell me about Python")

for delta in provider.stream_chat(session.get_messages()):
    if delta.content:
        print(delta.content, end="", flush=True)
print()
```

For async:

```python
session.add_user_message("Tell me more")

async for delta in provider.astream_chat(session.get_messages()):
    if delta.content:
        print(delta.content, end="", flush=True)
print()
```

## Inspecting a Session

```python
# Number of messages
print(session)  # Session(5 messages)

# Get a copy of the message list
messages = session.get_messages()
```

!!! note
    `get_messages()` returns a **copy** of the message list, so modifying it won't affect the session.