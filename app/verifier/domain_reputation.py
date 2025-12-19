# backend/app/verifier/domain_reputation.py

from datetime import datetime, timedelta

# ⚠️ En memoria por ahora (luego DB / Redis)
DOMAIN_HISTORY = {}

# -------------------------------
# Update domain reputation
# -------------------------------
def update_domain_reputation(domain: str, result: dict):
    now = datetime.utcnow()

    if domain not in DOMAIN_HISTORY:
        DOMAIN_HISTORY[domain] = {
            "total_checks": 0,
            "deliverable": 0,
            "undeliverable": 0,
            "risky": 0,
            "unknown": 0,
            "last_seen": now
        }

    stats = DOMAIN_HISTORY[domain]
    stats["total_checks"] += 1
    stats["last_seen"] = now

    status = result.get("status")
    if status in stats:
        stats[status] += 1


# -------------------------------
# Compute reputation score
# -------------------------------
def get_domain_reputation_score(domain: str) -> int:
    stats = DOMAIN_HISTORY.get(domain)
    if not stats:
        return 0

    score = 0
    total = stats["total_checks"]

    if total < 5:
        return 0  # poca data, no influye

    deliverable_ratio = stats["deliverable"] / total
    undeliverable_ratio = stats["undeliverable"] / total
    risky_ratio = stats["risky"] / total

    # Penalizaciones fuertes
    score -= int(undeliverable_ratio * 50)
    score -= int(risky_ratio * 20)

    # Bonificación
    score += int(deliverable_ratio * 40)

    return score


# -------------------------------
# Domain trust level
# -------------------------------
def get_domain_trust_level(domain: str) -> str:
    score = get_domain_reputation_score(domain)

    if score >= 30:
        return "high"
    if score >= 10:
        return "medium"
    if score > 0:
        return "low"
    return "unknown"
