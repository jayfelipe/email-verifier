def email_scoring(dns_result: dict, smtp_result: dict, heuristics: dict):
    score = 100
    reasons = []

    # ------------------------
    # 1. DNS / MX checks
    # ------------------------
    if not dns_result.get("has_mx", False):
        score -= 80
        reasons.append("Domain has no MX records")

    if dns_result.get("mx_suspicious", False):
        score -= 25
        reasons.append("MX records appear suspicious")


    # ------------------------
    # 2. SMTP checks
    # ------------------------
    smtp_status = smtp_result.get("status")

    if smtp_status == "undeliverable":
        score -= 90
        reasons.append("SMTP returned 550 – mailbox does not exist")

    elif smtp_status == "risky":
        score -= 40
        reasons.append("SMTP returned inconsistent result")

    elif smtp_status == "unknown":
        score -= 25
        reasons.append("SMTP uncertain – could not verify user")


    # timeouts
    t = smtp_result.get("timeouts", 0)
    if t > 0:
        score -= min(30 * t, 60)  # cap
        reasons.append(f"{t} SMTP timeouts detected")

    # greylisting
    g = smtp_result.get("greylist_count", 0)
    if g > 2:
        score -= 40
        reasons.append("Severe greylisting")
    elif g > 0:
        score -= 10
        reasons.append("Greylisting detected")


    # tarpit
    if smtp_result.get("tarpit", False):
        score -= 40
        reasons.append("Tarpitting detected (slow responses)")


    # catch-all
    if heuristics["catch_all"]["is_catch_all"]:
        # detect if server is good or irregular
        server = heuristics["server_fingerprint"]["provider"]
        if server in ("google", "outlook", "zoho"):
            score -= 20
            reasons.append("Catch-all domain but reputable server")
        else:
            score -= 45
            reasons.append("Catch-all domain with unknown server")


    # ------------------------
    # 3. Heuristics
    # ------------------------

    # disposable domain
    if heuristics["disposable"]["is_disposable"]:
        score -= 70
        reasons.append("Disposable domain")

    # alias
    if heuristics["alias"]["has_alias"]:
        score -= 2
        reasons.append("Alias (+tag) detected")

    # role account
    if heuristics["role_account"]["is_role"]:
        score -= 10
        reasons.append(f"Role account: {heuristics['role_account']['role_type']}")

    # private relay (Apple, Firefox, etc.)
    if heuristics["private_relay"]["is_private_relay"]:
        score -= 25
        reasons.append("Private relay / masked email")


    # ------------------------
    # 4. Server fingerprint bonus
    # ------------------------
    fp_provider = heuristics["server_fingerprint"]["provider"]
    conf = heuristics["server_fingerprint"]["confidence"]

    if fp_provider in ("google", "outlook", "zoho", "protonmail"):
        score += 10
        reasons.append(f"High reputation provider: {fp_provider}")

    elif conf > 60:
        score += 5
        reasons.append("Known SMTP banner – moderate confidence")


    # ------------------------
    # Final normalization
    # ------------------------
    if score > 100:
        score = 100
    if score < 0:
        score = 0

    # ------------------------
    # Classification
    # ------------------------
    if score >= 90:
        quality = "high"
        status = "deliverable"
        action = "accept"
    elif score >= 70:
        quality = "medium"
        status = "risky"
        action = "review"
    elif score >= 40:
        quality = "low"
        status = "risky"
        action = "review"
    else:
        quality = "bad"
        status = "undeliverable"
        action = "reject"

    return {
        "score": score,
        "quality": quality,
        "status": status,
        "reasons": reasons,
        "recommended_action": action
    }
