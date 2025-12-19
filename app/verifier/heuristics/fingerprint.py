SERVER_PATTERNS = {
    "google": ["gmail", "google", "mx.google.com"],
    "outlook": ["outlook", "hotmail", "protection.outlook.com"],
    "zoho": ["zoho"],
    "protonmail": ["protonmail"],
    "yahoo": ["yahoo"]
}

def fingerprint_server(banner: str | None):
    if not banner:
        return {"provider": None, "confidence": 0, "banner": None}

    banner_l = banner.lower()

    for provider, patterns in SERVER_PATTERNS.items():
        for p in patterns:
            if p in banner_l:
                return {
                    "provider": provider,
                    "confidence": 90,
                    "banner": banner
                }

    return {
        "provider": None,
        "confidence": 10,
        "banner": banner
    }
