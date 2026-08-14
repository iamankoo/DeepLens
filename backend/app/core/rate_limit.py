from fastapi import HTTPException, Request, status

from app.core.logger import logger
from app.queue.connection import redis_conn

# Fixed-window counter backed by Redis (already a hard dependency via RQ,
# so this adds no new infra) — INCR is atomic, so concurrent requests from
# the same client can't race past the limit. Keyed by client IP: the auth
# endpoints this guards (login, register, forgot-password, ...) are
# unauthenticated by definition, so IP is the only identity available
# before the request body proves anything.


def rate_limit(*, key_prefix: str, limit: int, window_seconds: int):
    async def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        redis_key = f"deeplens:ratelimit:{key_prefix}:{client_ip}"

        current = redis_conn.incr(redis_key)
        if current == 1:
            redis_conn.expire(redis_key, window_seconds)

        if current > limit:
            ttl = redis_conn.ttl(redis_key)
            retry_after = ttl if ttl and ttl > 0 else window_seconds
            logger.warning(
                "rate limit exceeded",
                extra={"key_prefix": key_prefix, "client_ip": client_ip, "limit": limit, "count": current},
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
