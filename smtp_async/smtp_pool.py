# smtp_async/smtp_pool.py
import asyncio
import aiosmtplib
from contextlib import asynccontextmanager
from collections import defaultdict

class SMTPConnectionPool:
    def __init__(self, max_connections_per_domain=3):
        self.max = max_connections_per_domain
        self.pools = defaultdict(list)
        self.locks = defaultdict(asyncio.Lock)

    async def _create_connection(self, mx_host):
        return await aiosmtplib.SMTP(
            hostname=mx_host,
            port=25,
            timeout=10
        ).connect()

    @asynccontextmanager
    async def acquire(self, mx_host):
        async with self.locks[mx_host]:
            if self.pools[mx_host]:
                conn = self.pools[mx_host].pop()
            else:
                conn = await self._create_connection(mx_host)

        try:
            yield conn
        finally:
            async with self.locks[mx_host]:
                if len(self.pools[mx_host]) < self.max:
                    self.pools[mx_host].append(conn)
                else:
                    await conn.quit()
