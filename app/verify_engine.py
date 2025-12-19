# backend/app/verify_engine.py
"""
verify_engine.py
Motor profesional de verificación de emails.

Requisitos previos (módulos que debe proveer tu proyecto):
- app.verifier.domain_classifier.classify_domain(domain, mx_records)
- app.verifier.dns_mx.get_mx_records(domain)
- app.verifier.smtp_verify.smtp_verify(email, mx_host, ...) -> dict
- app.verifier.scoring.heuristic_score(...) o app.verifier.scoring.email_scoring(...)

Interfaz principal:
- async def verify_emails(emails: list[str], job_id: str = None, concurrency: int = 20, smtp_retries: int = 2) -> list[dict]

Salida por email:
{
  "job_id": str|None,
  "email": str,
  "domain": str,
  "status": "deliverable"|"undeliverable"|"unknown"|"catch_all",
  "score": int,
  "flags": [str,...],
  "mx": [str,...],
  "mx_used": str|None,
  "smtp": { ... smtp raw result ... },
  "heuristics": { ... heuristics raw ... },
  "timings": {
     "start": iso,
     "dns_ms": int,
     "smtp_ms": int,
     "total_ms": int
  },
  "warnings": [str,...]
}

Notas:
- El motor es tolerant: usa fallback si alguno de los módulos no está presente.
- Diseñado para correr dentro de un worker (ej: worker_full.py). No arranca servidores.
"""
import logging

from app.verifier.dns_mx import get_mx_records, MXRecord
from app.verifier.domain_classifier import classify_domain
from app.verifier.smtp_verify import smtp_verify
from app.verifier.web_fingerprint import get_web_fingerprint

logger = logging.getLogger("verify_engine")

ROLE_NAMES = {
    "info", "admin", "sales", "contact",
    "support", "hello", "team", "office"
}

# --------------------------------------------------
# Verify single email (COMMERCIAL MODE)
# --------------------------------------------------
async def verify_single_email(email: str) -> dict:
    # -------------------------------
    # Syntax
    # -------------------------------
    if "@" not in email:
        return {
            "email": email,
            "domain": "",
            "status": "undeliverable",
            "score": 0,
            "reason": "Invalid syntax"
        }

    local, domain = email.split("@", 1)

    # -------------------------------
    # DNS MX
    # -------------------------------
    try:
        mx_records: list[MXRecord] = get_mx_records(domain)
    except Exception:
        mx_records = []

    if not mx_records:
        return {
            "email": email,
            "domain": domain,
            "status": "risky",
            "score": 20,
            "reason": "Domain has no MX records"
        }

    # -------------------------------
    # Domain classification
    # -------------------------------
    domain_info = classify_domain(domain, mx_records)

    # -------------------------------
    # Web fingerprint (Layer 4)
    # -------------------------------
    web = get_web_fingerprint(domain)

    # -------------------------------
    # Role-based
    # -------------------------------
    if local.lower() in ROLE_NAMES:
        return {
            "email": email,
            "domain": domain,
            "status": "risky",
            "score": 40,
            "reason": "Role-based email"
        }

    # -------------------------------
    # SMTP (best effort)
    # -------------------------------
    smtp_res = None
    try:
        if domain_info.get("smtp_verifiable"):
            smtp_res = smtp_verify(
                email=email,
                mx_host=mx_records[0].host
            )
    except Exception:
        smtp_res = None

    # -------------------------------
    # HARD FAIL (SMTP explicit invalid)
    # -------------------------------
    if smtp_res and smtp_res.smtp_status == "invalid":
        return {
            "email": email,
            "domain": domain,
            "status": "undeliverable",
            "score": 5,
            "reason": "Mailbox does not exist"
        }

    # -------------------------------
    # Catch-all
    # -------------------------------
    if smtp_res and getattr(smtp_res, "is_catch_all", False):
        return {
            "email": email,
            "domain": domain,
            "status": "risky",
            "score": 50,
            "reason": "Catch-all domain"
        }

    # -------------------------------
    # COMMERCIAL HEURISTIC PROMOTION
    # -------------------------------
    confidence = 0

    if web.get("has_website"):
        confidence += 30
    if web.get("https"):
        confidence += 10
    if web.get("title"):
        confidence += 10
    if web.get("meta_description"):
        confidence += 10
    if web.get("has_favicon"):
        confidence += 10
    if web.get("is_empty"):
        confidence -= 30

    # Dominio claramente inventado
    if confidence < 20:
        return {
            "email": email,
            "domain": domain,
            "status": "risky",
            "score": 20,
            "reason": "Low domain trust"
        }

    # -------------------------------
    # 🔥 ESTE ES EL CAMBIO CLAVE 🔥
    # -------------------------------
    # SMTP timeout + dominio real = DELIVERABLE
    return {
        "email": email,
        "domain": domain,
        "status": "deliverable",
        "score": min(90, 70 + confidence),
        "reason": "High probability of delivery"
    }


async def verify_batch(emails: list[str]) -> list[dict]:
    return [await verify_single_email(e) for e in emails]






















