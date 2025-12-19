# backend/app/verifier/heuristics/heuristics.py

from disposable import check_disposable
from role import check_role_account
from alias import check_alias
from private_relay import check_private_relay
from fingerprint import fingerprint_server
from risk import evaluate_risk

def analyze_heuristics(email: str, domain: str, smtp: dict, mx_exists: bool) -> dict:
    """
    Analiza riesgo heurístico del email.
    Compatible con worker_full.py
    Combina heurísticas básicas + heurísticas avanzadas del engine.
    """

    # --- Separar local y dominio ---
    local, domain_part = email.split("@")
    domain = domain or domain_part

    # --- Heurísticas tipo engine ---
    disposable = check_disposable(domain)
    role_acc = check_role_account(local)
    alias = check_alias(local)
    private_relay = check_private_relay(domain)

    server_fp = fingerprint_server(smtp.get("server_banner") if smtp else None)

    risk_signals = evaluate_risk({
        "greylist_count": smtp.get("greylist_count", 0) if smtp else 0,
        "timeouts": smtp.get("timeouts", 0) if smtp else 0,
        "tarpit_detected": smtp.get("tarpit", False) if smtp else False
    })

    catch_all_info = {
        "is_catch_all": smtp.get("is_catch_all", False) if smtp else False,
        "evidence": smtp.get("catch_all_reason", "") if smtp else ""
    }

    # --- Heurísticas tipo heuristics.py (score simplificado) ---
    score = 0
    flags = []

    # Dominio sospechoso
    if domain.endswith(".ru") or domain.endswith(".tk"):
        score += 30
        flags.append("suspicious_tld")

    # SMTP status
    smtp_status = smtp.get("smtp_status") if smtp else None
    if smtp_status == "deliverable":
        score += 5
    elif smtp_status == "risky":
        score += 25
        flags.append("smtp_risky")
    elif smtp_status == "undeliverable":
        score += 50
        flags.append("smtp_failed")

    if catch_all_info["is_catch_all"]:
        score += 15
        flags.append("catch_all_domain")

    # MX existence
    if not mx_exists:
        score += 50
        flags.append("missing_mx")

    # Determinar estado
    if score <= 10:
        status = "deliverable"
    elif score <= 40:
        status = "risky"
        flags.append("medium_risk")
    else:
        status = "undeliverable"

    # --- Resultado final ---
    return {
        "disposable": disposable,
        "catch_all": catch_all_info,
        "role_account": role_acc,
        "alias": alias,
        "private_relay": private_relay,
        "server_fingerprint": server_fp,
        "risk_signals": risk_signals,
        "score": score,
        "status": status,
        "flags": flags
    }
