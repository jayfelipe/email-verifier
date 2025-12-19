# backend/app/verifier/domain_classifier.py

FREE_PROVIDERS = {
    "gmail.com", "googlemail.com",
    "outlook.com", "hotmail.com",
    "yahoo.com", "icloud.com",
    "protonmail.com", "gmx.com",
    "yandex.com"
}

INSTITUTIONAL_TLDS = (".edu", ".gov", ".mil")

def classify_domain(domain: str, mx_records: list) -> dict:
    domain = domain.lower()

    is_free = domain in FREE_PROVIDERS
    is_institutional = domain.endswith(INSTITUTIONAL_TLDS)

    if is_free:
        return {
            "provider": domain,
            "type": "unverifiable_personal",
            "smtp_verifiable": False
        }

    if is_institutional:
        return {
            "provider": domain,
            "type": "institutional",
            "smtp_verifiable": False
        }

    # Business domain
    return {
        "provider": domain,
        "type": "business",
        "smtp_verifiable": True
    }

