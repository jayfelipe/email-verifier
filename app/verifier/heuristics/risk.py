#risk.py
def evaluate_risk(signals):
    grey = signals.get("greylist_count", 0)
    timeouts = signals.get("timeouts", 0)
    tarpit = signals.get("tarpit_detected", False)

    risk_score = 0

    if grey > 2:
        risk_score += 30
    if timeouts > 2:
        risk_score += 40
    if tarpit:
        risk_score += 50

    level = "low"
    if 30 <= risk_score < 60:
        level = "medium"
    elif risk_score >= 60:
        level = "high"

    return {
        "greylisted": grey > 0,
        "greylist_count": grey,
        "tarpit_detected": tarpit,
        "timeouts": timeouts,
        "overall_risk": level
    }
