# backend/app/tests/conftest.py
import asyncio
import pytest
from httpx import AsyncClient
from ..main import app
import anyio

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as c:
        yield c
