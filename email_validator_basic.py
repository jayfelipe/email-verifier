"""
email_validator_basic.py
Módulo para:
- Validación de formato de email.
- Verificación DNS/MX con timeouts y caching simple.
"""

import re
import socket
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
from functools import lru_cache
import dns.resolver
import dns.exception

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email_validator_basic")

# ----------------------------
# 1 Validación de formato
# ----------------------------
# Regex razonable y práctica (no el RFC completo que es enorme).
# Esta regex evita caracteres inválidos y controla longitud básica.
EMAIL_REGEX = re.compile(
    r"^(?P<local>[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]{1,64})@(?P<domain>[A-Za-z0-9.-]{1,255})$"
)

ROLE_LOCALPARTS = {
    "postmaster", "abuse", "admin", "webmaster", "info", "support", "security"
}

def is_valid_format(email: str) -> bool:
    """
    Verifica formato básico del email.
    - Comprueba longitud de local-part y dominio.
    - Asegura que local-part y dominio cumplan patrón razonable.
    """
    if not email or "@" not in email:
        return False
    m = EMAIL_REGEX.match(email)
    if not m:
        return False
    local = m.group("local")
    domain = m.group("domain")

    # No permitir segmentos del dominio que empiecen o terminen con -
    for label in domain.split('.'):
        if not label or label.startswith('-') or label.endswith('-'):
            return False
        if len(label) > 63:
            return False

    # Longitud total del email
    if len(email) > 254:
        return False

    # No permitir local-part que empiece o termine con .
    if local.startswith('.') or local.endswith('.'):
        return False

    return True

def is_role_account(email: str) -> bool:
    """
    Heurística simple para detectar cuentas 'role' como info@, admin@, etc.
    """
    local = email.split('@', 1)[0].lower()
    # Si hay + alias, tomar la parte antes del +
    local = local.split('+', 1)[0]
    return local in ROLE_LOCALPARTS

# ----------------------------
# 2 DNS / MX checks
# ----------------------------

# Parámetros de tiempo / reintentos
DNS_TIMEOUT = 5.0  # segundos por consulta
DNS_RETRIES = 1

@lru_cache(maxsize=4096)
def get_mx_records(domain: str, timeout: float = DNS_TIMEOUT) -> Tuple[bool, List[Tuple[int, str]]]:
    """
    Retorna (success, list_of_mx) donde list_of_mx es lista de tuplas (preference, exchange)
    Cacheada para reducir queries repetidas. Maneja excepciones y timeouts.
    """
    resolver = dns.resolver.Resolver()
    resolver.lifetime = timeout
    resolver.timeout = timeout
    tries = DNS_RETRIES
    last_exception = None

    for attempt in range(tries + 1):
        try:
            # Query MX
            answers = resolver.resolve(domain, 'MX')
            mxs = []
            for r in answers:
                # r.preference, r.exchange
                pref = int(r.preference)
                exch = str(r.exchange).rstrip('.')  # quitar punto final
                mxs.append((pref, exch))
            # Ordenar por preference (menor es preferido)
            mxs.sort(key=lambda x: x[0])
            return True, mxs
        except dns.resolver.NoAnswer:
            # No hay registros MX; muchos dominios usan A records en lugar de MX.
            last_exception = dns.resolver.NoAnswer()
            break
        except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers) as e:
            last_exception = e
            break
        except dns.exception.Timeout as e:
            last_exception = e
            logger.debug(f"Timeout resolviendo MX para {domain}: intento {attempt}: {e}")
        except Exception as e:
            last_exception = e
            logger.debug(f"Error resolviendo MX para {domain}: {e}")

    # Si no hay MX, intentar resolver registro A como fallback
    try:
        answers = resolver.resolve(domain, 'A')
        a_records = [str(r) for r in answers]
        # Simular MX con prioridad alta (ej. 0)
        mxs = [(0, domain)]
        return True, mxs
    except Exception as e:
        logger.debug(f"Fallback A record fallo para {domain}: {e}")
        # Si tuvimos excepción previa, loggear
        logger.info(f"No se pudo resolver MX/A para dominio {domain}: {last_exception or e}")
        return False, []

# ----------------------------
# 3 Función pública compuesta
# ----------------------------

@dataclass
class MXCheckResult:
    domain: str
    has_mx: bool
    mx_records: List[Tuple[int, str]]
    error: Optional[str] = None

@dataclass
class FormatCheckResult:
    email: str
    valid_format: bool
    is_role: bool
    domain: Optional[str] = None

def check_format_and_mx(email: str, dns_timeout: float = DNS_TIMEOUT) -> Tuple[FormatCheckResult, MXCheckResult]:
    """
    Realiza la validación de formato y luego MX lookup.
    Retorna tuplas con resultados detallados.
    """
    email = email.strip()
    format_ok = is_valid_format(email)
    domain = None
    is_role_acc = False
    if format_ok:
        domain = email.split('@', 1)[1].lower()
        is_role_acc = is_role_account(email)

    fmt_res = FormatCheckResult(
        email=email,
        valid_format=format_ok,
        is_role=is_role_acc,
        domain=domain
    )

    if not format_ok:
        mx_res = MXCheckResult(domain="", has_mx=False, mx_records=[], error="Formato inválido")
        return fmt_res, mx_res

    try:
        success, mxs = get_mx_records(domain, timeout=dns_timeout)
        if success and mxs:
            mx_res = MXCheckResult(domain=domain, has_mx=True, mx_records=mxs)
        else:
            mx_res = MXCheckResult(domain=domain, has_mx=False, mx_records=[], error="No MX/A records")
    except Exception as e:
        mx_res = MXCheckResult(domain=domain, has_mx=False, mx_records=[], error=str(e))

    return fmt_res, mx_res

# ----------------------------
# 4) Ejemplo de uso / pruebas rápidas
# ----------------------------
if __name__ == "__main__":
    tests = [
        "johndoe@example.com",
        "info@github.com",
        "invalid-email@@example..com",
        "user+alias@sub.domain.co",
        "no-mx@domain-que-no-existe-xyz-12345.com"
    ]

    for t in tests:
        fmt, mx = check_format_and_mx(t)
        print("----")
        print("Email:", fmt.email)
        print("Formato válido:", fmt.valid_format)
        if fmt.valid_format:
            print("Es role account:", fmt.is_role)
            print("Dominio:", fmt.domain)
        print("Has MX:", mx.has_mx)
        print("MX Records:", mx.mx_records)
        if mx.error:
            print("Error MX:", mx.error)
