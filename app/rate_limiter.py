import time
import math
import os
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/2")
r = redis.from_url(REDIS_URL, decode_responses=True)

def token_bucket_key(prefix: str, identifier: str):
    return f"rl:{prefix}:{identifier}"

def allow_request(identifier: str, capacity: int, refill_rate_per_second: float):
    """
    Token bucket alg:
    - capacity: max tokens
    - refill_rate_per_second: tokens added per second
    Returns True if allowed, else False.
    Implementación atomic aprox usando GET/SET con timestamps (no Lua por simplicidad).
    """
    key = token_bucket_key("tb", identifier)
    now = time.time()
    item = r.hgetall(key)
    if not item:
        # inicializar
        r.hset(key, mapping={"tokens": capacity - 1, "last": now})
        r.expire(key, 3600)
        return True

    tokens = float(item.get("tokens", capacity))
    last = float(item.get("last", now))
    # recalculate tokens
    delta = now - last
    tokens = min(capacity, tokens + delta * refill_rate_per_second)
    if tokens >= 1:
        tokens -= 1
        r.hset(key, mapping={"tokens": tokens, "last": now})
        r.expire(key, 3600)
        return True
    else:
        # no hay tokens, actualizar last
        r.hset(key, mapping={"tokens": tokens, "last": now})
        r.expire(key, 3600)
        return False

# Circuit breaker
def breaker_key(identifier: str):
    return f"cb:{identifier}"

def increment_failure(identifier: str, window_seconds=300, threshold=5, open_seconds=300):
    """
    Increment failure count; if threshold exceeded, open circuit for open_seconds.
    Returns True if circuit is open after increment.
    """
    key = breaker_key(identifier)
    pipe = r.pipeline()
    pipe.incr(key + ":count")
    pipe.expire(key + ":count", window_seconds)
    count, _ = pipe.execute()
    if int(count) >= threshold:
        # open circuit
        r.set(key + ":open", 1, ex=open_seconds)
        return True
    return False

def is_open(identifier: str):
    return r.exists(breaker_key(identifier) + ":open") == 1

def clear_failures(identifier: str):
    r.delete(breaker_key(identifier) + ":count", breaker_key(identifier) + ":open")
