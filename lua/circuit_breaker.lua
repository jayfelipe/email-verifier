-- file: lua/circuit_breaker.lua
-- KEYS[1] = key_prefix (e.g. "cb:domain")
-- ARGV: window_seconds, threshold, open_seconds, now, action
-- action = "inc" or "is_open" or "clear"
local prefix = KEYS[1]
local window = tonumber(ARGV[1])
local threshold = tonumber(ARGV[2])
local open_secs = tonumber(ARGV[3])
local now = tonumber(ARGV[4])
local action = ARGV[5]

local count_key = prefix .. ":count"
local open_key = prefix .. ":open_until"

if action == "inc" then
  local cnt = redis.call("INCR", count_key)
  redis.call("EXPIRE", count_key, window)
  if tonumber(cnt) >= threshold then
    local until_ts = now + open_secs
    redis.call("SET", open_key, until_ts, "EX", open_secs)
    return {1, tonumber(cnt), until_ts}
  end
  return {0, tonumber(cnt), 0}
elseif action == "is_open" then
  local until = redis.call("GET", open_key)
  if not until then
    return {0, 0}
  end
  until = tonumber(until)
  if until > now then
    return {1, until}
  else
    -- expired, clear
    redis.call("DEL", open_key)
    redis.call("DEL", count_key)
    return {0, 0}
  end
elseif action == "clear" then
  redis.call("DEL", open_key)
  redis.call("DEL", count_key)
  return {1}
else
  return {-1, "invalid_action"}
end
