# backend/app/tasks.py
import os
import json
import uuid
import logging
from typing import List, Dict, Any

try:
    import redis
except Exception:
    redis = None

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_QUEUE_KEY = os.environ.get("REDIS_QUEUE_KEY", "email_jobs")

# Lazy init redis client to avoid side-effects at import time
_redis_client = None

def _get_redis():
    global _redis_client
    if _redis_client is None:
        if redis is None:
            raise RuntimeError("redis package not installed in venv")
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client

def enqueue_job(job_id: str, owner_id: int, emails: List[str], meta: Dict[str, Any] = None) -> str:
    """
    Encola un job en Redis (lista). Retorna job_id.
    NO hace imports circulares ni inicializa workers.
    """
    payload = {
        "job_id": job_id or str(uuid.uuid4()),
        "owner_id": owner_id,
        "emails": emails,
        "meta": meta or {}
    }

    # ❌ Protección para Redis caído
    try:
        r = _get_redis()
        r.rpush(REDIS_QUEUE_KEY, json.dumps(payload))
        logger.info("Enqueued job %s (%d emails)", payload["job_id"], len(emails))
    except Exception as e:
        logger.warning(f"Redis no disponible, job no encolado: {e}")

    return payload["job_id"]

# ✅ Procesar job directamente sin worker
async def process_job_direct(job_id: str, owner_id: int, emails: List[str]):
    """
    Procesa un job directamente sin worker.
    """
    from .verifier import verify_email_full
    from .crud import insert_result, update_job_processed

    for email in emails:
        result = await verify_email_full(email)

        await insert_result({
            "job_id": job_id,
            "email": email,
            "domain": result.get("domain"),
            "smtp": result.get("smtp_status"),
            "heuristics": json.dumps(result.get("heuristics")),
            "scoring": str(result.get("score"))
        })

        await update_job_processed(job_id, 1)
