import asyncio
import aioredis
from smtp_async.worker import AsyncWorker

async def fake_validate(email, conn):
    await asyncio.sleep(0.1)
    print("validated", email)

async def test_end_to_end():
    redis = aioredis.from_url("redis://localhost")

    worker = AsyncWorker(redis, fake_validate)

    domain_map = {
        "example.com": "fake-smtp"
    }

    asyncio.create_task(worker.start(domain_map))

    for i in range(50):
        await worker.batcher.add_email("example.com", f"user{i}@example.com")

    await asyncio.sleep(3)
