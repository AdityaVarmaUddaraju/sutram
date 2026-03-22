"""Provider registry and factory."""

import logging
from typing import Callable, Literal

from .cache import Cache
from .config import APIConfig, RetryPolicy, RequestConfig
from .base import BaseProvider

logger = logging.getLogger(__name__)

PROVIDER_REGISTRY: dict[str, dict] = {}

def register_provider(name: str, base_url: str | None = None):
    """Decorator to register a provider class."""
    def decorator(cls):
        if not issubclass(cls, BaseProvider):
            raise TypeError(f"{cls.__name__} must be a subclass of BaseProvider")
        PROVIDER_REGISTRY[name] = {"cls": cls, "base_url": base_url}
        logger.debug(f"Registered provider: {name}")
        return cls
    return decorator

def create_provider(
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
    sync_client=None,
    async_client=None,
    verify: bool | str = True,
) -> BaseProvider:
    if name not in PROVIDER_REGISTRY:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDER_REGISTRY.keys())}")

    entry = PROVIDER_REGISTRY[name]
    logger.info(f"Creating provider: {name} ({model})")

    url = base_url or entry.get("base_url")
    if not url:
        raise ValueError(f"No base_url provided for provider: {name}")

    api_config = APIConfig(
        base_url=url,
        api_key=api_key,
        retry_policy=RetryPolicy(
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            strategy=strategy,
            timeout=timeout,
            retry_on_status=retry_on_status or [429, 500, 502, 503, 504],
        ),
    )

    request_config = RequestConfig(
        api_config=api_config,
        sync_client=sync_client,
        async_client=async_client,
        verify=verify,
    )

    return entry["cls"](model=model, request_config=request_config, cache=cache)
