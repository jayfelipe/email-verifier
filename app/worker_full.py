# backend/app/worker_full.py
"""
Worker completo: consume jobs de Redis, ejecuta pipeline (DNS->SMTP->Heuristics->Scoring)
y persiste resultados en la tabla emailresult vía CRUD async existente.

Cómo correr:
    cd backend
    python -m app.worker_full

Requiere:
    - redis (redis-py >= 4)
    - asyncio
    - que tu archivo app/crud.py exponga insert_result() y update_job_processed()
    - que existan (opcional) app.verifier.dns_mx.get_mx_records
                         app.verifier.smtp_verify.smtp_verify (async or sync)
                         app.verifier.heuristics.analyze_heuristics
                         app.verifier.heuristics.scoring.email_scoring
Si no existen, el worker usa implementaciones fallback sencillas para pruebas.
"""

# backend/app/worker_full.py

import os
import json
import asyncio
import logging

# Redis
try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None

# Motor central
try:
    from app.verify_engine import verify_batch
except Exception as e:
    print("ERROR cargando verify_engine:", e)
    verify_batch = None

# DB CRUD
try:
    from app.crud import insert_result, update_job_processed
except Exception:
    insert_result = None
    update_job_processed = None

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker_full")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_QUEUE_KEY = os.environ.get("REDIS_QUEUE_KEY", "email_jobs")
WORKER_SLEEP_EMPTY = float(os.environ.get("WORKER_SLEEP_EMPTY", "1.0"))
WORKER_CONCURRENCY = int(os.environ.get("WORKER_CONCURRENCY", "10"))

# --------------------------------------------------
# Normalización final (corregido)
# --------------------------------------------------
def normalize_result(raw: dict) -> dict:
    """
    Normaliza cualquier resultado basándose en status (no reason).
    Status permitidos: deliverable, risky, undeliverable, unknown
    """
    email = raw.get("email")
    status = raw.get("status", "unknown")
    score = raw.get("score", 0)
    reason = raw.get("reason", "SMTP connection timeout")

    if status == "deliverable":
        return {
            "Email Address": email,
            "Status": "deliverable",
            "Quality Score": min(100, score),
            "Reason": reason
        }

    if status == "undeliverable":
        return {
            "Email Address": email,
            "Status": "undeliverable",
            "Quality Score": score,
            "Reason": reason
        }

    if status == "risky":
        return {
            "Email Address": email,
            "Status": "risky",
            "Quality Score": score,
            "Reason": reason
        }

    return {
        "Email Address": email,
        "Status": "unknown",
        "Quality Score": score,
        "Reason": reason
    }

# --------------------------------------------------
# Persistencia en DB
# --------------------------------------------------
async def persist_result(job_id: str, result: dict):
    row = {
        "job_id": job_id,
        "email": result.get("Email Address"),
        "status": result.get("Status"),
        "score": result.get("Quality Score"),
        "reason": result.get("Reason"),
        "domain": result.get("domain") or (result["Email Address"].split("@", 1)[1] if "@" in result["Email Address"] else ""),
    }

    if insert_result is None:
        logger.info("DB insert skipped (insert_result missing)")
        return

    try:
        await insert_result(row)
    except Exception as e:
        logger.exception("Failed inserting result: %s", e)

# --------------------------------------------------
# Pipeline por email
# --------------------------------------------------
async def verify_email_pipeline(job_id: str, email: str):
    if verify_batch is None:
        raise RuntimeError("verify_engine.verify_batch no cargado")

    # verify_batch retorna resultado ya con status correcto
    results = await verify_batch([email])
    raw = results[0]

    # Normalización final basada en status
    normalized = normalize_result(raw)

    await persist_result(job_id, normalized)

    if update_job_processed:
        try:
            await update_job_processed(job_id, 1)
        except Exception:
            logger.exception("Failed update_job_processed")

    return normalized

# --------------------------------------------------
# Loop principal del worker
# --------------------------------------------------
async def consume_loop():
    logger.info("Starting worker_full consume loop (async)")

    if aioredis is None:
        logger.error("redis.asyncio missing. Install redis>=4.2")
        return

    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Connected to Redis %s", REDIS_URL)

    while True:
        try:
            item = await r.blpop(REDIS_QUEUE_KEY, timeout=5)
            if not item:
                await asyncio.sleep(WORKER_SLEEP_EMPTY)
                continue

            _, raw = item
            try:
                payload = json.loads(raw)
            except Exception:
                logger.exception("Invalid payload, skipping")
                continue

            job_id = payload.get("job_id")
            emails = payload.get("emails", [])

            logger.info("Received job %s with %d emails", job_id, len(emails))

            # Concurrency control
            sem = asyncio.Semaphore(WORKER_CONCURRENCY)
            async def sem_task(e):
                async with sem:
                    return await verify_email_pipeline(job_id, e)

            tasks = [asyncio.create_task(sem_task(e)) for e in emails]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, Exception):
                    logger.exception("Pipeline error: %s", res)
                else:
                    logger.info(
                        f"Result: {res['Email Address']} -> "
                        f"status={res.get('Status')} | "
                        f"score={res.get('Quality Score')} | "
                        f"reason={res.get('Reason')}"
                    )

            logger.info("Job %s finished", job_id)

        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Worker loop exception")
            await asyncio.sleep(1)


def main():
    logger.info("Worker full starting (CTRL+C to stop)")
    asyncio.run(consume_loop())


if __name__ == "__main__":
    main()


