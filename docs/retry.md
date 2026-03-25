# Retry Policies

Retry policies handle transient API failures automatically, so your application recovers gracefully from timeouts, rate limits, and server errors.

## Default Behavior

By default, providers make a single attempt with no retries:

```python
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
)
```

## Enabling Retries

```python
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
    max_retries=3,
)
```

This will retry up to 3 times on failures, for a total of 4 attempts.

## Backoff Strategies

### Exponential (default)

Wait time doubles with each attempt: 1s → 2s → 4s → 8s...

```python
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
    max_retries=3,
    strategy="exponential",
    backoff_factor=1.0,  # base wait time in seconds
)
```

| Attempt | Wait Time |
|---------|-----------|
| 1 | 1.0s |
| 2 | 2.0s |
| 3 | 4.0s |

### Fixed

Same wait time between every attempt:

```python
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
    max_retries=3,
    strategy="fixed",
    backoff_factor=2.0,  # wait 2s between each attempt
)
```

## Retryable Status Codes

By default, retries are triggered on these HTTP status codes:

| Code | Meaning |
|------|---------|
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |
| 504 | Gateway Timeout |

Customize which status codes trigger a retry:

```python
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
    max_retries=3,
    retry_on_status=[429, 503],
)
```

## Timeouts

Set the request timeout in seconds:

```python
provider = create_provider(
    name="openrouter",
    model="openai/gpt-4",
    api_key="your-api-key",
    timeout=60,  # 60 second timeout
)
```

Timeouts also trigger retries if `max_retries > 0`.

## Retries and Streaming

For streaming requests (`stream_llm`, `stream_chat`, etc.), retries only apply **before the stream opens**. If the connection fails or returns a retryable status code, the request is retried. Once data starts flowing, no further retries are attempted — this prevents sending duplicate partial content to the consumer.

## Debugging

Enable logging to see retry activity:

```python
import logging

logging.basicConfig(level=logging.INFO)
```

You'll see messages like:

```
INFO:sutram.base:Request to openai/gpt-4 (attempt 1/4)
WARNING:sutram.base:Status 429, retrying in 1.0s
INFO:sutram.base:Request to openai/gpt-4 (attempt 2/4)
INFO:sutram.base:Request successful (200)
```