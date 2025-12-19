import time
import fakeredis
import redis
import os
from app.redis_scripts import TOKEN_BUCKET_LUA

# We'll use fakeredis for testing but need to load lua script into fakeredis server
def test_token_bucket_allow_and_refill(tmp_path, monkeypatch):
    # start fake redis
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/2")  # optional
    # load script into fakeredis
    sha = fake.script_load(TOKEN_BUCKET_LUA)
    key = "tb:testdomain"
    now = time.time()
    # call script: EVALSHA sha 1 key capacity refill now requested
    res = fake.evalsha(sha, 1, key, 5, 1.0, now, 1)
    assert res[0] == 1
    # tokens decreased
    assert float(res[1]) <= 4.0
    # consume remaining tokens
    for i in range(4):
        res = fake.evalsha(sha, 1, key, 5, 1.0, now, 1)
    # next should be denied
    res = fake.evalsha(sha, 1, key, 5, 1.0, now, 1)
    assert res[0] == 0
    # advance time to refill
    later = now + 3
    res = fake.evalsha(sha, 1, key, 5, 1.0, later, 1)
    assert res[0] == 1
