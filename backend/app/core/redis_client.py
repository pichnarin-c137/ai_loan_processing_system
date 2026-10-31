from functools import lru_cache

from redis import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry

from app.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    # redis-py retries 10 times by default, which would turn the 2s timeouts into ~25s.
    return Redis.from_url(
        get_settings().redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
        retry=Retry(NoBackoff(), 0),
    )
