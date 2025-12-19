# smtp_async/batcher.py
import asyncio
from collections import defaultdict

class DomainBatcher:
    def __init__(self, batch_size=20, max_wait_ms=400):
        self.queues = defaultdict(asyncio.Queue)
        self.batch_size = batch_size
        self.max_wait = max_wait_ms / 1000

    async def add_email(self, domain, email):
        await self.queues[domain].put(email)

    async def next_batch(self, domain):
        q = self.queues[domain]
        batch = []

        try:
            item = await asyncio.wait_for(q.get(), timeout=self.max_wait)
            batch.append(item)
        except asyncio.TimeoutError:
            return []

        start = asyncio.get_event_loop().time()
        while len(batch) < self.batch_size:
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= self.max_wait:
                break
            try:
                item = await asyncio.wait_for(q.get(), timeout=self.max_wait - elapsed)
                batch.append(item)
            except asyncio.TimeoutError:
                break

        return batch
