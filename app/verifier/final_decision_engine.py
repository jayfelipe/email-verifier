# backend/app/verifier/final_decision_engine.py

def decide(signal: dict) -> dict:
    # 1. Invalid syntax → evidencia dura
    if not signal.get("syntax_valid", False):
        return result(signal, "undeliverable", 0, "Invalid syntax")

    # 2. Disposable domain → siempre risky
    if signal.get("is_disposable", False):
        return result(signal, "risky", 40, "Disposable domain")

    # 3. SMTP explícito: mailbox no existe → evidencia dura (raro)
    if signal.get("smtp_result") == "mailbox_not_found":
        return result(signal, "undeliverable", 10, "Mailbox does not exist")

    # 4. SMTP explícito: mailbox existe
    if signal.get("smtp_result") == "mailbox_exists":
        return result(signal, "deliverable", 95, "SMTP mailbox exists")

    # 5. Catch-all domain
    if signal.get("is_catch_all", False):
        return result(signal, "risky", 60, "Catch-all domain")

    # 6. Role-based email
    if signal.get("is_role", False):
        return result(signal, "risky", 50, "Role-based email")

    # 7. Free providers (Gmail, Outlook, Yahoo, etc.)
    # Nunca undeliverable por heurística
    if signal.get("is_free_provider", False):
        username_strength = signal.get("username_strength", "normal")

        if username_strength == "weak":
            return result(
                signal,
                "risky",
                55,
                "Low confidence username on free provider"
            )

        if username_strength == "normal":
            return result(
                signal,
                "deliverable",
                85,
                "Free provider heuristic deliverable"
            )

        # strong
        return result(
            signal,
            "deliverable",
            95,
            "Free provider heuristic deliverable"
        )

    # 8. SMTP timeout (dominios corporativos normalmente)
    if signal.get("smtp_timed_out", False):
        return result(signal, "unknown", 30, "SMTP connection timeout")

    # 9. Fallback seguro
    return result(signal, "unknown", 25, "Insufficient data")


def result(signal: dict, status: str, score: int, reason: str) -> dict:
    return {
        "email": signal.get("email"),
        "status": status,
        "quality_score": score,
        "reason": reason
    }
