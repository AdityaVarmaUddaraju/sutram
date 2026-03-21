"""Caching layer for LLM responses."""

import logging
from typing import Protocol
from hashlib import sha256
import json

logger = logging.getLogger(__name__)

class Cache(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...

class DictCache:
    def __init__(self):
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        result = self._store.get(key)
        if result is not None:
            logger.debug(f"Cache hit: {key[:12]}...")
        return result

    def set(self, key: str, value: str) -> None:
        self._store[key] = value
        logger.debug(f"Cache set: {key[:12]}...")

def make_cache_key(model: str, messages: list[dict]) -> str:
    raw = f"{model}::{json.dumps(messages, sort_keys=True)}"
    return sha256(raw.encode()).hexdigest()
