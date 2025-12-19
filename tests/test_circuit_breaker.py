import time
import fakeredis
from app.redis_scripts import CB_LUA

def test_circuit_breaker(tmp_path, monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    sha = fake.script_load(open("lua/circuit_breaker.lua").read())
    key = "cb:testdomain"
    now = int(time.time())
    # increment 1..threshold
    for i in range(4):
        res = fake.evalsha(sha, 1, key, 60, 5, 30, now, "inc")
        assert res[1] == i+1
    # threshold at 5
    res = fake.evalsha(sha, 1, key, 60, 5, 30, now, "inc")
    assert res[0] == 1  # opened
    is_open = fake.evalsha(sha, 1, key, 0,0,0,now,"is_open")
    assert is_open[0] == 1
    # clear
    fake.evalsha(sha, 1, key, 0,0,0,now,"clear")
    is_open = fake.evalsha(sha, 1, key, 0,0,0,now,"is_open")
    assert is_open[0] == 0
