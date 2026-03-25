"""Base provider with caching, retry, and sync/async support."""

import asyncio
import json
import logging
import time
from contextlib import contextmanager, asynccontextmanager
from collections.abc import Generator, AsyncGenerator

import httpx

from .cache import Cache, make_cache_key
from .config import APIConfig, RequestConfig, ResponseSchema, ToolConfig
from .response import LLMResponse, StreamDelta, Usage, ToolCall

logger = logging.getLogger(__name__)

class BaseProvider:
    """Subclasses implement _build_request_body(), _parse_response(), and _parse_stream_chunk()."""

    def __init__(self, model: str, request_config: RequestConfig, cache: Cache | None = None):
        self.model = model
        self.request_config = request_config
        self.cache = cache

    @property
    def api_config(self) -> APIConfig:
        return self.request_config.api_config

    def _build_request_body(self, messages: list[dict], response_format: dict | None = None, tool_config: ToolConfig | None = None) -> dict:
        raise NotImplementedError

    def _build_response_format(self, response_model) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "schema": response_model.model_json_schema(),
            },
        }

    def _parse_response(self, data: dict) -> LLMResponse:
        raise NotImplementedError

    def _parse_stream_chunk(self, data: dict) -> StreamDelta:
        """Subclasses implement this to parse a single SSE chunk."""
        raise NotImplementedError

    @staticmethod
    def _parse_sse_line(line: str) -> dict | None:
        """Parse an SSE line into JSON, or None if it should be skipped."""
        if not line.startswith("data: ") or line == "data: [DONE]":
            return None
        return json.loads(line[6:])

    def _assemble_response(self, deltas: list[StreamDelta]) -> LLMResponse:
        """Assemble a list of StreamDeltas into a complete LLMResponse."""
        content = "".join(d.content for d in deltas if d.content)
        finish_reason = next((d.finish_reason for d in reversed(deltas) if d.finish_reason), None)
        usage = next((d.usage for d in reversed(deltas) if d.usage), Usage())
        return LLMResponse(content=content or None, finish_reason=finish_reason, usage=usage)

    def _build_messages(self, prompt: str, system_prompt: str | None = None) -> list[dict]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    # --- Cache helpers ---
    def _cache_get(self, messages: list[dict]) -> LLMResponse | None:
        if self.cache is None: return None
        data = self.cache.get(make_cache_key(self.model, messages))
        if data is None: return None
        return LLMResponse.model_validate_json(data)

    def _cache_set(self, messages: list[dict], result: LLMResponse) -> None:
        if self.cache is None: return
        self.cache.set(make_cache_key(self.model, messages), result.model_dump_json())

    # --- Sync request with retry ---
    def _request_with_retry(self, messages: list[dict], response_format: dict | None = None, tool_config: ToolConfig | None = None) -> LLMResponse:
        policy = self.api_config.retry_policy
        api_key = self.api_config.get_api_key()
        body = self._build_request_body(messages, response_format=response_format, tool_config=tool_config)
        last_error = None
        client = self.request_config.sync_client
        should_close = client is None
        if should_close:
            client = httpx.Client(verify=self.request_config.verify)

        try:
            for attempt in range(policy.max_retries + 1):
                try:
                    logger.info(f"Request to {self.model} (attempt {attempt+1}/{policy.max_retries+1})")
                    response = client.post(
                        self.api_config.base_url,
                        headers={"Authorization": f"Bearer {api_key}"},
                        json=body,
                        timeout=policy.timeout,
                    )
                    if response.status_code in policy.retry_on_status and attempt < policy.max_retries:
                        wait = policy.get_wait_time(attempt)
                        logger.warning(f"Status {response.status_code}, retrying in {wait:.1f}s")
                        time.sleep(wait)
                        continue
                    response.raise_for_status()
                    logger.info(f"Request successful ({response.status_code})")
                    return self._parse_response(response.json())
                except httpx.TimeoutException as e:
                    last_error = e
                    if attempt < policy.max_retries:
                        wait = policy.get_wait_time(attempt)
                        logger.warning(f"Timeout, retrying in {wait:.1f}s")
                        time.sleep(wait)
        finally:
            if should_close:
                client.close()

        logger.error(f"All {policy.max_retries+1} attempts failed")
        raise last_error or RuntimeError("Max retries exceeded")

    # --- Async request with retry ---
    async def _arequest_with_retry(self, messages: list[dict], response_format: dict | None = None, tool_config: ToolConfig | None = None) -> LLMResponse:
        policy = self.api_config.retry_policy
        api_key = await self.api_config.aget_api_key()
        body = self._build_request_body(messages, response_format=response_format, tool_config=tool_config)
        last_error = None
        client = self.request_config.async_client
        should_close = client is None
        if should_close:
            client = httpx.AsyncClient(verify=self.request_config.verify)

        try:
            for attempt in range(policy.max_retries + 1):
                try:
                    logger.info(f"Async request to {self.model} (attempt {attempt+1}/{policy.max_retries+1})")
                    response = await client.post(
                        self.api_config.base_url,
                        headers={"Authorization": f"Bearer {api_key}"},
                        json=body,
                        timeout=policy.timeout,
                    )
                    if response.status_code in policy.retry_on_status and attempt < policy.max_retries:
                        wait = policy.get_wait_time(attempt)
                        logger.warning(f"Status {response.status_code}, retrying in {wait:.1f}s")
                        await asyncio.sleep(wait)
                        continue
                    response.raise_for_status()
                    logger.info(f"Async request successful ({response.status_code})")
                    return self._parse_response(response.json())
                except httpx.TimeoutException as e:
                    last_error = e
                    if attempt < policy.max_retries:
                        wait = policy.get_wait_time(attempt)
                        logger.warning(f"Timeout, retrying in {wait:.1f}s")
                        await asyncio.sleep(wait)
        finally:
            if should_close:
                await client.aclose()

        logger.error(f"All {policy.max_retries+1} attempts failed")
        raise last_error or RuntimeError("Max retries exceeded")

    # --- Parse with retry ---
    def _parse_with_retry(self, messages: list[dict], response: LLMResponse, schema: ResponseSchema) -> LLMResponse:
        response_format = self._build_response_format(schema.response_model)
        for attempt in range(schema.max_parse_retries + 1):
            try:
                response.parsed = schema.response_model.model_validate_json(response.content)
                return response
            except Exception as e:
                if attempt >= schema.max_parse_retries:
                    raise ValueError(f"Failed to parse response after {schema.max_parse_retries + 1} attempts: {e}")
                logger.warning(f"Parse attempt {attempt+1} failed: {e}")
                messages = messages + [
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": f"Your response did not match the required schema. Error: {e}. Please try again."},
                ]
                response = self._request_with_retry(messages, response_format=response_format)
        return response

    async def _aparse_with_retry(self, messages: list[dict], response: LLMResponse, schema: ResponseSchema) -> LLMResponse:
        response_format = self._build_response_format(schema.response_model)
        for attempt in range(schema.max_parse_retries + 1):
            try:
                response.parsed = schema.response_model.model_validate_json(response.content)
                return response
            except Exception as e:
                if attempt >= schema.max_parse_retries:
                    raise ValueError(f"Failed to parse response after {schema.max_parse_retries + 1} attempts: {e}")
                logger.warning(f"Parse attempt {attempt+1} failed: {e}")
                messages = messages + [
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": f"Your response did not match the required schema. Error: {e}. Please try again."},
                ]
                response = await self._arequest_with_retry(messages, response_format=response_format)
        return response

    # --- Sync stream with retry ---
    @contextmanager
    def _open_stream(self, client: httpx.Client, body: dict):
        """Retry loop that yields a successful streaming response."""
        policy = self.api_config.retry_policy
        last_error = None
        for attempt in range(policy.max_retries + 1):
            try:
                logger.info(f"Stream request to {self.model} (attempt {attempt+1}/{policy.max_retries+1})")
                with client.stream(
                    "POST", self.api_config.base_url,
                    headers={"Authorization": f"Bearer {self.api_config.get_api_key()}"},
                    json=body, timeout=policy.timeout,
                ) as response:
                    if response.status_code in policy.retry_on_status and attempt < policy.max_retries:
                        wait = policy.get_wait_time(attempt)
                        logger.warning(f"Status {response.status_code}, retrying in {wait:.1f}s")
                        time.sleep(wait)
                        continue
                    response.raise_for_status()
                    yield response
                    return
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < policy.max_retries:
                    wait = policy.get_wait_time(attempt)
                    logger.warning(f"Timeout, retrying in {wait:.1f}s")
                    time.sleep(wait)
        raise last_error or RuntimeError("Max retries exceeded")

    def _stream_with_retry(self, messages: list[dict], tool_config: ToolConfig | None = None) -> Generator[StreamDelta, None, None]:
        cached = self._cache_get(messages)
        if cached:
            yield StreamDelta(content=cached.content, finish_reason=cached.finish_reason)
            return

        body = self._build_request_body(messages, tool_config=tool_config)
        body["stream"] = True

        client = self.request_config.sync_client
        should_close = client is None
        if should_close:
            client = httpx.Client(verify=self.request_config.verify)

        try:
            with self._open_stream(client, body) as response:
                deltas = []
                for line in response.iter_lines():
                    data = self._parse_sse_line(line)
                    if data is None: continue
                    delta = self._parse_stream_chunk(data)
                    deltas.append(delta)
                    yield delta
                self._cache_set(messages, self._assemble_response(deltas))
        finally:
            if should_close:
                client.close()

    # --- Async stream with retry ---
    @asynccontextmanager
    async def _aopen_stream(self, client: httpx.AsyncClient, body: dict):
        """Async retry loop that yields a successful streaming response."""
        policy = self.api_config.retry_policy
        last_error = None
        for attempt in range(policy.max_retries + 1):
            try:
                logger.info(f"Async stream request to {self.model} (attempt {attempt+1}/{policy.max_retries+1})")
                async with client.stream(
                    "POST", self.api_config.base_url,
                    headers={"Authorization": f"Bearer {await self.api_config.aget_api_key()}"},
                    json=body, timeout=policy.timeout,
                ) as response:
                    if response.status_code in policy.retry_on_status and attempt < policy.max_retries:
                        wait = policy.get_wait_time(attempt)
                        logger.warning(f"Status {response.status_code}, retrying in {wait:.1f}s")
                        await asyncio.sleep(wait)
                        continue
                    response.raise_for_status()
                    yield response
                    return
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < policy.max_retries:
                    wait = policy.get_wait_time(attempt)
                    logger.warning(f"Timeout, retrying in {wait:.1f}s")
                    await asyncio.sleep(wait)
        raise last_error or RuntimeError("Max retries exceeded")

    async def _astream_with_retry(self, messages: list[dict], tool_config: ToolConfig | None = None) -> AsyncGenerator[StreamDelta, None]:
        cached = self._cache_get(messages)
        if cached:
            yield StreamDelta(content=cached.content, finish_reason=cached.finish_reason)
            return

        body = self._build_request_body(messages, tool_config=tool_config)
        body["stream"] = True

        client = self.request_config.async_client
        should_close = client is None
        if should_close:
            client = httpx.AsyncClient(verify=self.request_config.verify)

        try:
            async with self._aopen_stream(client, body) as response:
                deltas = []
                async for line in response.aiter_lines():
                    data = self._parse_sse_line(line)
                    if data is None: continue
                    delta = self._parse_stream_chunk(data)
                    deltas.append(delta)
                    yield delta
                self._cache_set(messages, self._assemble_response(deltas))
        finally:
            if should_close:
                await client.aclose()

    # --- Sync API ---
    def call_llm(self, prompt: str, system_prompt: str | None = None, response_schema: ResponseSchema | None = None, tool_config: ToolConfig | None = None) -> LLMResponse:
        messages = self._build_messages(prompt, system_prompt)
        response_format = self._build_response_format(response_schema.response_model) if response_schema else None
        cached = self._cache_get(messages)
        if cached is not None: return cached
        result = self._request_with_retry(messages, response_format=response_format, tool_config=tool_config)
        if response_schema:
            result = self._parse_with_retry(messages, result, response_schema)
        self._cache_set(messages, result)
        return result

    def chat(self, messages: list[dict], response_schema: ResponseSchema | None = None, tool_config: ToolConfig | None = None) -> LLMResponse:
        response_format = self._build_response_format(response_schema.response_model) if response_schema else None
        cached = self._cache_get(messages)
        if cached is not None: return cached
        result = self._request_with_retry(messages, response_format=response_format, tool_config=tool_config)
        if response_schema:
            result = self._parse_with_retry(messages, result, response_schema)
        self._cache_set(messages, result)
        return result

    # --- Async API ---
    async def acall_llm(self, prompt: str, system_prompt: str | None = None, response_schema: ResponseSchema | None = None, tool_config: ToolConfig | None = None) -> LLMResponse:
        messages = self._build_messages(prompt, system_prompt)
        response_format = self._build_response_format(response_schema.response_model) if response_schema else None
        cached = self._cache_get(messages)
        if cached is not None: return cached
        result = await self._arequest_with_retry(messages, response_format=response_format, tool_config=tool_config)
        if response_schema:
            result = await self._aparse_with_retry(messages, result, response_schema)
        self._cache_set(messages, result)
        return result

    async def achat(self, messages: list[dict], response_schema: ResponseSchema | None = None, tool_config: ToolConfig | None = None) -> LLMResponse:
        response_format = self._build_response_format(response_schema.response_model) if response_schema else None
        cached = self._cache_get(messages)
        if cached is not None: return cached
        result = await self._arequest_with_retry(messages, response_format=response_format, tool_config=tool_config)
        if response_schema:
            result = await self._aparse_with_retry(messages, result, response_schema)
        self._cache_set(messages, result)
        return result

    # --- Sync Streaming API ---
    def stream_llm(self, prompt: str, system_prompt: str | None = None, tool_config: ToolConfig | None = None) -> Generator[StreamDelta, None, None]:
        messages = self._build_messages(prompt, system_prompt)
        yield from self._stream_with_retry(messages, tool_config=tool_config)

    def stream_chat(self, messages: list[dict], tool_config: ToolConfig | None = None) -> Generator[StreamDelta, None, None]:
        yield from self._stream_with_retry(messages, tool_config=tool_config)

    # --- Async Streaming API ---
    async def astream_llm(self, prompt: str, system_prompt: str | None = None, tool_config: ToolConfig | None = None) -> AsyncGenerator[StreamDelta, None]:
        messages = self._build_messages(prompt, system_prompt)
        async for delta in self._astream_with_retry(messages, tool_config=tool_config):
            yield delta

    async def astream_chat(self, messages: list[dict], tool_config: ToolConfig | None = None) -> AsyncGenerator[StreamDelta, None]:
        async for delta in self._astream_with_retry(messages, tool_config=tool_config):
            yield delta
