# backend/app/tasks.py
import os
import json
import uuid
import logging
from typing import List, Dict, Any

import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_QUEUE_KEY = os.environ.get("REDIS_QUEUE_KEY", "email_jobs")

_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def enqueue_job(
    job_id: str,
    owner_id: int | None,
    emails: List[str],
    meta: Dict[str, Any] | None = None
) -> str:
    payload = {
        "job_id": job_id or str(uuid.uuid4()),
        "owner_id": owner_id,
        "emails": emails,
        "meta": meta or {}
    }

    r = get_redis()
    r.rpush(REDIS_QUEUE_KEY, json.dumps(payload))

    logger.info(
        "Job enqueued %s (%d emails)",
        payload["job_id"],
        len(emails)
    )

    return payload["job_id"]

