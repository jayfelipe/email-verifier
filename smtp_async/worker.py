# smtp_async/worker.py
import asyncio
from smtp_async.smtp_pool import SMTPConnectionPool
from smtp_async.batcher import DomainBatcher
from smtp_async.redis_lua import RateLimiter

class AsyncWorker:
    def __init__(self, redis, validate_smtp_func):
        self.redis = redis
        self.batcher = DomainBatcher()
        self.pool = SMTPConnectionPool()
        self.validate_smtp = validate_smtp_func
        self.rate = RateLimiter(redis)

    async def process_domain(self, domain, mx_host):
        while True:
            batch = await self.batcher.next_batch(domain)
            if not batch:
                continue

            allowed = await self.rate.allow(domain)
            if not allowed:
                await asyncio.sleep(0.5)
                continue

            async with self.pool.acquire(mx_host) as conn:
                tasks = [self.validate_smtp(email, conn) for email in batch]
                await asyncio.gather(*tasks)

    async def start(self, domain_to_mx):
        await self.rate.load()

        tasks = [
            asyncio.create_task(self.process_domain(domain, mx))
            for domain, mx in domain_to_mx.items()
        ]

        await asyncio.gather(*tasks)
