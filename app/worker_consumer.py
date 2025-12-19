# backend/app/worker_consumer.py
import os
import time
import json
import logging
from typing import Dict, Any

import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_QUEUE_KEY = os.environ.get("REDIS_QUEUE_KEY", "email_jobs")
SLEEP_ON_EMPTY = 1.0

logger = logging.getLogger("worker")
r = redis.from_url(REDIS_URL, decode_responses=True)

def process_job(payload: Dict[str, Any]):
    """
    Aquí llamas a tu pipeline real (DNS -> SMTP -> heuristics -> scoring).
    Para la demo solo printamos.
    """
    job_id = payload.get("job_id")
    emails = payload.get("emails", [])
    logger.info("Processing job %s with %d emails", job_id, len(emails))
    # TODO: llamar a tu lógica verify_email(...) por cada email (o batch)
    # from .verifier.verify import verify_email
    # for e in emails: verify_email(e)
    time.sleep(0.1 * len(emails))
    logger.info("Finished job %s", job_id)


def run():
    logger.info("Worker consumer started, listening on %s", REDIS_QUEUE_KEY)
    while True:
        item = r.blpop(REDIS_QUEUE_KEY, timeout=5)  # returns (key, value) or None
        if not item:
            time.sleep(SLEEP_ON_EMPTY)
            continue
        _, raw = item
        try:
            payload = json.loads(raw)
        except Exception as exc:
            logger.exception("Invalid payload in queue: %s", raw)
            continue
        try:
            process_job(payload)
        except Exception:
            logger.exception("Failed processing job %s", payload.get("job_id"))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
