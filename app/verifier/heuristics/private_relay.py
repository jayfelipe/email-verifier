PRIVATE_PROVIDERS = {
    "privaterelay.appleid.com": "apple",
    "duck.com": "duckduckgo",
    "simplelogin.co": "simplelogin",
    "relay.firefox.com": "firefox",
    "pm.me": "protonmail"
}

def check_private_relay(domain: str):
    domain = domain.lower()
    for d, provider in PRIVATE_PROVIDERS.items():
        if domain.endswith(d):
            return {
                "is_private_relay": True,
                "provider": provider
            }

    return {
        "is_private_relay": False,
        "provider": None
    }
