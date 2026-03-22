"""Base provider with caching, retry, and sync/async support."""

import asyncio
import logging
import time

import httpx

from .cache import Cache, make_cache_key
from .config import APIConfig, RequestConfig, ResponseSchema
from .response import LLMResponse, Usage, ToolCall

logger = logging.getLogger(__name__)

class BaseProvider:
    """Subclasses implement _build_request_body() and _parse_response()."""

    def __init__(self, model: str, request_config: RequestConfig, cache: Cache | None = None):
        self.model = model
        self.request_config = request_config
        self.cache = cache

    @property
    def api_config(self) -> APIConfig:
        return self.request_config.api_config

    def _build_request_body(self, messages: list[dict], response_format: dict | None = None) -> dict:
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
    def _request_with_retry(self, messages: list[dict], response_format: dict | None = None) -> LLMResponse:
        policy = self.api_config.retry_policy
        api_key = self.api_config.get_api_key()
        body = self._build_request_body(messages, response_format=response_format)
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
    async def _arequest_with_retry(self, messages: list[dict], response_format: dict | None = None) -> LLMResponse:
        policy = self.api_config.retry_policy
        api_key = await self.api_config.aget_api_key()
        body = self._build_request_body(messages, response_format=response_format)
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

    # --- Sync API ---
    def call_llm(self, prompt: str, system_prompt: str | None = None, response_schema: ResponseSchema | None = None) -> LLMResponse:
        messages = self._build_messages(prompt, system_prompt)
        response_format = self._build_response_format(response_schema.response_model) if response_schema else None
        cached = self._cache_get(messages)
        if cached is not None: return cached
        result = self._request_with_retry(messages, response_format=response_format)
        if response_schema:
            result = self._parse_with_retry(messages, result, response_schema)
        self._cache_set(messages, result)
        return result

    def chat(self, messages: list[dict], response_schema: ResponseSchema | None = None) -> LLMResponse:
        response_format = self._build_response_format(response_schema.response_model) if response_schema else None
        cached = self._cache_get(messages)
        if cached is not None: return cached
        result = self._request_with_retry(messages, response_format=response_format)
        if response_schema:
            result = self._parse_with_retry(messages, result, response_schema)
        self._cache_set(messages, result)
        return result

    # --- Async API ---
    async def acall_llm(self, prompt: str, system_prompt: str | None = None, response_schema: ResponseSchema | None = None) -> LLMResponse:
        messages = self._build_messages(prompt, system_prompt)
        response_format = self._build_response_format(response_schema.response_model) if response_schema else None
        cached = self._cache_get(messages)
        if cached is not None: return cached
        result = await self._arequest_with_retry(messages, response_format=response_format)
        if response_schema:
            result = await self._aparse_with_retry(messages, result, response_schema)
        self._cache_set(messages, result)
        return result

    async def achat(self, messages: list[dict], response_schema: ResponseSchema | None = None) -> LLMResponse:
        response_format = self._build_response_format(response_schema.response_model) if response_schema else None
        cached = self._cache_get(messages)
        if cached is not None: return cached
        result = await self._arequest_with_retry(messages, response_format=response_format)
        if response_schema:
            result = await self._aparse_with_retry(messages, result, response_schema)
        self._cache_set(messages, result)
        return result
