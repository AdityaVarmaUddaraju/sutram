"""Configuration models for providers."""

import asyncio
import logging
from typing import Callable, Literal
import inspect

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_factor: float = 1.0
    strategy: Literal["exponential", "fixed"] = "exponential"
    timeout: int = 120
    retry_on_status: list[int] = [429, 500, 502, 503, 504]

    def get_wait_time(self, attempt: int) -> float:
        if self.strategy == "fixed":
            return self.backoff_factor
        return self.backoff_factor * (2 ** attempt)

class APIConfig(BaseModel):
    base_url: str
    api_key: str | Callable[[], str]
    retry_policy: RetryPolicy = RetryPolicy()

    model_config = {"arbitrary_types_allowed": True}

    def get_api_key(self) -> str:
        if callable(self.api_key):
            return self.api_key()
        return self.api_key

    async def aget_api_key(self) -> str:
        if callable(self.api_key):
            if inspect.iscoroutinefunction(self.api_key):
                return await self.api_key()
            return self.api_key()
        return self.api_key

class RequestConfig(BaseModel):
    api_config: APIConfig
    sync_client: httpx.Client | None = None
    async_client: httpx.AsyncClient | None = None

    model_config = {"arbitrary_types_allowed": True}
