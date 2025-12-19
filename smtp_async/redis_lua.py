# smtp_async/redis_lua.py
import aioredis

TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local capacity = tonumber(ARGV[3])

local data = redis.call("HMGET", key, "tokens", "last")
local tokens = tonumber(data[1])
local last = tonumber(data[2])

if not tokens then
    tokens = capacity
    last = now
end

local delta = now - last
local refill = delta * refill_rate
tokens = math.min(capacity, tokens + refill)

if tokens < 1 then
    redis.call("HMSET", key, "tokens", tokens, "last", now)
    return 0
elseif tokens > 0 then
    redis.call("HMSET", key, "tokens", tokens - 1, "last", now)
    return 1
end
"""

class RateLimiter:
    def __init__(self, redis):
        self.redis = redis
        self.script = None

    async def load(self):
        self.script = await self.redis.script_load(TOKEN_BUCKET_LUA)

    async def allow(self, domain):
        now = int(asyncio.get_event_loop().time())
        return await self.redis.evalsha(
            self.script,
            keys=[f"bucket:{domain}"],
            args=[now, 10, 20]  # refill_rate=10/s, capacity=20
        )
