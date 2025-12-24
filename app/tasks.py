# backend/app/tasks.py
import os
import json
import uuid
import logging
from typing import List, Dict, Any

import redis

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ==============================
# Variables de entorno (OBLIGATORIAS)
# ==============================

REDIS_URL = os.environ.get("REDIS_URL")
REDIS_QUEUE_KEY = os.environ.get("REDIS_QUEUE_KEY", "email_jobs")

if not REDIS_URL:
    raise RuntimeError("❌ REDIS_URL no está definida en las variables de entorno")

# ==============================
# Cliente Redis (lazy init)
# ==============================

_redis_client = None

def _get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True
        )
    return _redis_client

# ==============================
# Encolar job (API → Redis)
# ==============================

def enqueue_job(
    job_id: str,
    owner_id: int,
    emails: List[str],
    meta: Dict[str, Any] | None = None
) -> str:
    """
    Encola un job en Redis para que el worker lo procese.
    SI Redis falla → la API debe fallar (no se oculta el error).
    """

    payload = {
        "job_id": job_id or str(uuid.uuid4()),
        "owner_id": owner_id,
        "emails": emails,
        "meta": meta or {}
    }

    try:
        r = _get_redis()
        r.rpush(REDIS_QUEUE_KEY, json.dumps(payload))
        logger.info(
            "✅ Job encolado: %s (%d emails)",
            payload["job_id"],
            len(emails)
        )
    except Exception as e:
        logger.exception("❌ Error encolando job en Redis")
        raise RuntimeError("Redis no disponible, no se pudo encolar el job") from e

    return payload["job_id"]
