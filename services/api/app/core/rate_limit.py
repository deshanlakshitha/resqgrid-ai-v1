"""Bounded request throttling shared through Redis, with a local outage fallback."""

import asyncio
import hashlib
import time

import structlog
from fastapi import HTTPException, Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = structlog.get_logger()
_client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
_lock = asyncio.Lock()
_local: dict[str, tuple[int, float]] = {}
_retry_redis_at = 0.0
_INCREMENT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return {count, redis.call('TTL', KEYS[1])}
"""


def client_identity(request: Request) -> str:
    # Trust only the ASGI peer resolved by the server's trusted-proxy settings.
    return request.client.host if request.client else "unknown"


async def enforce_rate_limit(scope: str, identity: str, limit: int, window: int) -> None:
    global _retry_redis_at
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    key = f"resqgrid:limit:{scope}:{digest}"
    now = time.monotonic()
    count = None
    retry_after = window
    if now >= _retry_redis_at:
        try:
            count, retry_after = await _client.eval(_INCREMENT, 1, key, window)
        except (RedisError, OSError):
            _retry_redis_at = now + 30
            logger.warning("Rate limiter using bounded per-process fallback; Redis unavailable")
    if count is None:
        async with _lock:
            expired = [item for item, (_, deadline) in _local.items() if deadline <= now]
            for item in expired:
                _local.pop(item, None)
            if key not in _local and len(_local) >= 10_000:
                raise HTTPException(429, "Too many requests. Try again later.", headers={"Retry-After": "60"})
            previous, deadline = _local.get(key, (0, now + window))
            count = previous + 1
            _local[key] = (count, deadline)
            retry_after = max(1, int(deadline - now))
    if count > limit:
        raise HTTPException(
            429, "Too many requests. Try again later.",
            headers={"Retry-After": str(max(1, retry_after))},
        )


async def limit_auth_source(request: Request) -> None:
    registration = request.url.path.rstrip("/").endswith("/register")
    await enforce_rate_limit(
        "register-source" if registration else "auth-source",
        client_identity(request), 10 if registration else 60, 3600 if registration else 300,
    )
