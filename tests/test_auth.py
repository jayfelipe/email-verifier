# backend/app/tests/test_auth.py
import pytest

async def test_register_and_login(client):
    # register
    resp = await client.post("/auth/register", json={"email":"test@example.com", "password":"secret123"})
    assert resp.status_code in (200, 201)
    # login
    data = {"username":"test@example.com", "password":"secret123"}
    resp = await client.post("/auth/token", data=data)
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
