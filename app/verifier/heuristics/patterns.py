import re

ROLE_ACCOUNTS = [
    "admin", "support", "info", "sales", "contact",
    "help", "staff", "billing", "webmaster", "newsletter"
]

INVALID_PATTERNS = [
    r"\.\.",           # doble punto
    r"^-",             # empieza con guion
    r"-$",             # termina con guion
    r"[^A-Za-z0-9._%+-]"  # caracteres extraños
]

def is_role_account(email: str) -> bool:
    local = email.split("@")[0].lower()
    return local in ROLE_ACCOUNTS


def looks_like_invalid_pattern(email: str) -> bool:
    for pattern in INVALID_PATTERNS:
        if re.search(pattern, email):
            return True
    return False
