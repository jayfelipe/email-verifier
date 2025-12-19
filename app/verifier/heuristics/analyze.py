from .patterns import looks_like_invalid_pattern, is_role_account
from .disposable import is_disposable_domain
from .scoring import heuristic_score

COMMON_PROVIDERS = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com"]

def analyze_heuristics(email: str, smtp: dict, mx_exists: bool) -> dict:
    local, domain = email.split("@")

    flags = []

    smtp_status = smtp.get("status") if smtp else "unknown"

    # Score real desde scoring.py
    score = heuristic_score(
        email=email,
        smtp_status=smtp_status,
        has_mx=mx_exists
    )

    # Flags informativas
    if not mx_exists:
        flags.append("no_mx")

    if is_disposable_domain(domain):
        flags.append("disposable_domain")

    if looks_like_invalid_pattern(local):
        flags.append("suspicious_pattern")

    if is_role_account(local):
        flags.append("role_account")

    # Ajuste por proveedor confiable
    if domain in COMMON_PROVIDERS and score < 100:
        score += 5

    score = max(0, min(score, 100))

    # Mapeo status CORRECTO
    if score >= 80:
        status = "deliverable"
    elif score >= 40:
        status = "risky"
    else:
        status = "undeliverable"

    return {
        "score": score,
        "status": status,
        "flags": flags
    }


