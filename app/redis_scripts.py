import os
import time
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/2")
r = redis.from_url(REDIS_URL, decode_responses=True)

# Cargar scripts (script text loaded from files or inline)
TOKEN_BUCKET_LUA = open("lua/token_bucket.lua").read()
CB_LUA = open("lua/circuit_breaker.lua").read()

token_bucket_sha = r.script_load(TOKEN_BUCKET_LUA)
cb_sha = r.script_load(CB_LUA)

def allow_tokens(identifier: str, capacity: int, refill_per_sec: float, tokens: int = 1):
    key = f"tb:{identifier}"
    now = time.time()
    # EVALSHA returns [allowed(1/0), tokens_left]
    res = r.evalsha(token_bucket_sha, 1, key, capacity, refill_per_sec, now, tokens)
    return bool(int(res[0])), float(res[1])

def cb_increment(identifier: str, window_seconds: int, threshold: int, open_seconds: int):
    key = f"cb:{identifier}"
    now = int(time.time())
    res = r.evalsha(cb_sha, 1, key, window_seconds, threshold, open_seconds, now, "inc")
    # res: {is_open(1/0), count, until_ts}
    return {"is_open": bool(int(res[0])), "count": int(res[1]), "until": int(res[2])}

def cb_is_open(identifier: str):
    key = f"cb:{identifier}"
    now = int(time.time())
    res = r.evalsha(cb_sha, 1, key, 0, 0, 0, now, "is_open")
    return bool(int(res[0])), int(res[1])

def cb_clear(identifier: str):
    key = f"cb:{identifier}"
    res = r.evalsha(cb_sha, 1, key, 0, 0, 0, int(time.time()), "clear")
    return res
