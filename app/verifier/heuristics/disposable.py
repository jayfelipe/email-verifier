# disposable.py

DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "tempmail.com",
    "guerrillamail.com",
    "10minutemail.com",
    "trashmail.com",
    "yopmail.com"
}

def check_disposable(domain: str):
    domain = domain.lower().strip()

    if domain in DISPOSABLE_DOMAINS:
        return {
            "is_disposable": True,
            "provider": domain
        }

    # Coincidencias parciales (subdominios)
    for d in DISPOSABLE_DOMAINS:
        if domain.endswith(d):
            return {
                "is_disposable": True,
                "provider": d
            }

    return {
        "is_disposable": False,
        "provider": None
    }

# Aquí definimos la función EXACTA que espera __init__.py
def is_disposable_domain(domain: str) -> bool:
    return check_disposable(domain)["is_disposable"]

