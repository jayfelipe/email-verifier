import re

ROLE_NAMES = {
    "info", "admin", "sales", "contact", "support",
    "hello", "mail", "team", "office"
}

GENERIC_TEST_NAMES = {
    "test", "user", "demo", "example"
}

COMMON_HUMAN_NAMES = {
    # nombres comunes (EN / ES / LATAM)
    "carlos", "juan", "maria", "pedro", "jose",
    "andres", "luis", "ana", "laura", "david",
    "miguel", "sofia", "paula", "daniel"
}


def classify_username(local: str) -> str:
    local = local.lower().strip()

    # -------------------------------
    # Role-based
    # -------------------------------
    if local in ROLE_NAMES:
        return "role"

    # -------------------------------
    # Generic test users
    # -------------------------------
    if local in GENERIC_TEST_NAMES:
        return "generic"

    # -------------------------------
    # Known human names
    # -------------------------------
    if local in COMMON_HUMAN_NAMES:
        return "human"

    # -------------------------------
    # Human-like patterns
    # -------------------------------
    # nombre.apellido | nombreapellido
    if re.fullmatch(r"[a-z]{3,}\.[a-z]{3,}", local):
        return "human"

    if re.fullmatch(r"[a-z]{4,}", local):
        return "human"

    # -------------------------------
    # Random / machine generated
    # -------------------------------
    if re.search(r"\d{2,}", local):
        return "random"

    if re.search(r"[a-z]\d+[a-z]", local):
        return "random"

    # -------------------------------
    # Fallback
    # -------------------------------
    return "generic"

