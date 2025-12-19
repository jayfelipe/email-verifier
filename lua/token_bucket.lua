-- file: lua/token_bucket.lua
-- ARGV: capacity, refill_per_sec, now, requested_tokens
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local data = redis.call("HMGET", key, "tokens", "ts")
local tokens = tonumber(data[1])
local ts = tonumber(data[2])

if not tokens or not ts then
  tokens = capacity
  ts = now
end

-- refill tokens
local delta = math.max(0, now - ts)
local refill_amount = delta * refill
tokens = math.min(capacity, tokens + refill_amount)
ts = now

if tokens >= requested then
  tokens = tokens - requested
  redis.call("HMSET", key, "tokens", tokens, "ts", ts)
  redis.call("EXPIRE", key, 86400)
  return {1, tokens}
else
  redis.call("HMSET", key, "tokens", tokens, "ts", ts)
  redis.call("EXPIRE", key, 86400)
  return {0, tokens}
end
