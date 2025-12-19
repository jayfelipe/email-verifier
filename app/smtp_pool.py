import smtplib
import ssl
import threading
import time
from contextlib import contextmanager
from collections import defaultdict, deque

DEFAULT_TIMEOUT = 10

class SMTPConnection:
    def __init__(self, host, port=25, use_ssl=False, timeout=DEFAULT_TIMEOUT, helo_host="verifier.local"):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.helo_host = helo_host
        self.lock = threading.Lock()
        self.server = None
        self.last_used = 0
        self._connect()

    def _connect(self):
        if self.server:
            try:
                self.server.close()
            except Exception:
                pass
        ctx = ssl.create_default_context()
        if self.port == 465 or self.use_ssl:
            self.server = smtplib.SMTP_SSL(host=self.host, port=self.port, timeout=self.timeout, context=ctx)
        else:
            self.server = smtplib.SMTP(host=self.host, port=self.port, timeout=self.timeout)
        # EHLO
        try:
            self.server.ehlo(name=self.helo_host)
        except Exception:
            try:
                self.server.helo(name=self.helo_host)
            except Exception:
                pass
        self.last_used = time.time()

    def starttls_if_supported(self):
        try:
            if not isinstance(self.server, smtplib.SMTP_SSL) and self.server.has_extn('starttls'):
                self.server.starttls(context=ssl.create_default_context())
                self.server.ehlo(name=self.helo_host)
        except Exception:
            pass

    def mail_from(self, from_addr):
        # returns (code, msg)
        return self.server.mail(from_addr)

    def rcpt_to(self, rcpt):
        return self.server.rcpt(rcpt)

    def quit(self):
        try:
            self.server.quit()
        except Exception:
            try:
                self.server.close()
            except Exception:
                pass

class SMTPPool:
    def __init__(self, max_per_host=3, idle_timeout=60):
        self.max_per_host = max_per_host
        self.idle_timeout = idle_timeout
        self.pools = defaultdict(deque)  # host -> deque of SMTPConnection
        self._global_lock = threading.Lock()

    def _prune_idle(self):
        # close idle connections
        now = time.time()
        for host, dq in list(self.pools.items()):
            newdq = deque()
            while dq:
                conn = dq.popleft()
                if now - conn.last_used > self.idle_timeout:
                    try:
                        conn.quit()
                    except Exception:
                        pass
                else:
                    newdq.append(conn)
            self.pools[host] = newdq

    @contextmanager
    def get_connection(self, host, port=25, use_ssl=False, timeout=DEFAULT_TIMEOUT, helo_host="verifier.local"):
        self._prune_idle()
        dq = self.pools[host]
        conn = None
        # acquire or create
        with self._global_lock:
            while dq:
                candidate = dq.popleft()
                # test liveness
                try:
                    if time.time() - candidate.last_used > self.idle_timeout:
                        candidate.quit()
                        continue
                    conn = candidate
                    break
                except Exception:
                    continue
            if conn is None:
                conn = SMTPConnection(host=host, port=port, use_ssl=use_ssl, timeout=timeout, helo_host=helo_host)
        try:
            yield conn
        finally:
            conn.last_used = time.time()
            # return to pool if under limit
            with self._global_lock:
                dq = self.pools[host]
                if len(dq) < self.max_per_host:
                    dq.append(conn)
                else:
                    try:
                        conn.quit()
                    except Exception:
                        pass
