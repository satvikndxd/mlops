"""Redis-backed cache + rate limiter with graceful in-process fallback.

If ``AGENTFORGE_REDIS_URL`` is unset or Redis is unreachable, caching becomes a
no-op and rate limiting falls back to an in-process fixed-window counter, so
the platform runs identically (just without cross-process sharing) in dev/tests.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("cache")

_redis = None
_redis_ready = False
_fallback_buckets: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))


def _client():
    global _redis, _redis_ready
    if _redis_ready:
        return _redis
    _redis_ready = True
    if not settings.redis_url:
        logger.info("Redis disabled (no AGENTFORGE_REDIS_URL); using in-process fallback")
        _redis = None
        return None
    try:  # pragma: no cover - exercised only when redis is configured
        import redis as redis_lib

        client = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        _redis = client
        logger.info("Redis connected at %s", settings.redis_url)
    except Exception as exc:  # pragma: no cover
        logger.warning("Redis unavailable (%s); using in-process fallback", exc)
        _redis = None
    return _redis


def cache_get(key: str) -> Any | None:
    client = _client()
    if client is None:
        return None
    try:  # pragma: no cover - requires redis
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    client = _client()
    if client is None:
        return
    try:  # pragma: no cover - requires redis
        client.setex(key, ttl or settings.cache_ttl_seconds, json.dumps(value, default=str))
    except Exception:
        pass


def rate_limit_ok(identity: str, limit: int | None = None, window_seconds: int = 60) -> bool:
    """Fixed-window rate limit. Returns True if the call is allowed."""
    max_calls = limit or settings.rate_limit_per_minute
    client = _client()
    if client is not None:
        try:  # pragma: no cover - requires redis
            window = int(time.time() // window_seconds)
            key = f"rl:{identity}:{window}"
            count = client.incr(key)
            if count == 1:
                client.expire(key, window_seconds)
            return count <= max_calls
        except Exception:
            pass
    # In-process fallback.
    now = time.time()
    count, window_start = _fallback_buckets[identity]
    if now - window_start >= window_seconds:
        _fallback_buckets[identity] = (1, now)
        return True
    _fallback_buckets[identity] = (count + 1, window_start)
    return count + 1 <= max_calls


def reset_fallback() -> None:
    """Clear the in-process rate-limit buckets (used by tests)."""
    _fallback_buckets.clear()
