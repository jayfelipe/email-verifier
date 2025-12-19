import re
from email_validator import validate_email, EmailNotValidError

ROLE_ACCOUNTS = {
    "admin", "support", "contact", "info", "sales",
    "marketing", "help", "abuse", "security", "billing", "noreply"
}

def is_valid_format(email: str) -> bool:
    """
    Valida que el email tenga formato correcto según RFC y sintaxis estándar.
    Usa la librería 'email-validator' para validación robusta.
    """
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def is_role_account(email: str) -> bool:
    """
    Detecta cuentas de rol, como info@, admin@, support@.
    Retorna True si el email corresponde a un role account.
    """
    local_part = email.split("@")[0].lower()
    return local_part in ROLE_ACCOUNTS
