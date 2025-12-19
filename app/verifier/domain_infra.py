# backend/app/verifier/domain_infra.py

"""
Capa 3 – Infraestructura del dominio
----------------------------------
Este módulo NO verifica emails individuales.
Evalúa si un DOMINIO tiene infraestructura real para envío/recepción de correo.

Objetivo:
- Diferenciar dominios empresariales reales vs dominios inventados
- Reducir falsos positivos sin depender de SMTP RCPT TO
- Base para scoring tipo MyEmailVerification / Clearout
"""

import socket
import ssl
import datetime
import logging
import requests
import dns.resolver

try:
    import whois
except ImportError:
    whois = None

logger = logging.getLogger("domain_infra")

# --------------------------------------------------
# WHOIS – antigüedad del dominio
# --------------------------------------------------
def get_domain_age_days(domain: str) -> int | None:
    if not whois:
        return None

    try:
        w = whois.whois(domain)
        created = w.creation_date

        if isinstance(created, list):
            created = created[0]

        if not isinstance(created, datetime.date):
            return None

        return (datetime.datetime.utcnow().date() - created).days

    except Exception as e:
        logger.debug(f"WHOIS failed for {domain}: {e}")
        return None

# --------------------------------------------------
# SPF
# --------------------------------------------------
def has_spf(domain: str) -> bool:
    try:
        answers = dns.resolver.resolve(domain, "TXT")
        for rdata in answers:
            txt = "".join(part.decode() if isinstance(part, bytes) else part for part in rdata.strings)
            if txt.lower().startswith("v=spf1"):
                return True
    except Exception:
        pass
    return False

# --------------------------------------------------
# DMARC
# --------------------------------------------------
def has_dmarc(domain: str) -> bool:
    try:
        answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
        for rdata in answers:
            txt = "".join(part.decode() if isinstance(part, bytes) else part for part in rdata.strings)
            if txt.lower().startswith("v=dmarc1"):
                return True
    except Exception:
        pass
    return False

# --------------------------------------------------
# Web presence / parking detection (light)
# --------------------------------------------------
def check_web_presence(domain: str) -> str:
    urls = [f"https://{domain}", f"http://{domain}"]

    for url in urls:
        try:
            r = requests.get(url, timeout=4, allow_redirects=True)
            status = r.status_code
            text = (r.text or "").lower()

            if status >= 500:
                continue

            if any(x in text for x in [
                "buy this domain",
                "domain for sale",
                "parking",
                "sedo",
                "afternic",
                "godaddy cashparking",
            ]):
                return "parking"

            if status in (200, 301, 302) and len(text.strip()) > 200:
                return "active"

        except Exception:
            continue

    return "none"

# --------------------------------------------------
# HTTPS válido
# --------------------------------------------------
def has_valid_https(domain: str) -> bool:
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(3)
            s.connect((domain, 443))
            return True
    except Exception:
        return False

# --------------------------------------------------
# MASTER – evaluación completa de infraestructura
# --------------------------------------------------
def evaluate_domain_infra(domain: str) -> dict:
    age_days = get_domain_age_days(domain)
    spf = has_spf(domain)
    dmarc = has_dmarc(domain)
    web = check_web_presence(domain)
    https_ok = has_valid_https(domain)

    return {
        "domain": domain,
        "domain_age_days": age_days,
        "has_spf": spf,
        "has_dmarc": dmarc,
        "web_status": web,        # active | parking | none
        "https": https_ok,
    }

# --------------------------------------------------
# Helper para verify_engine.py
# --------------------------------------------------
def get_domain_infra(domain: str) -> dict:
    """
    Función simple para que verify_engine.py use
    solo la antigüedad y otras señales si se necesitan.
    """
    return evaluate_domain_infra(domain)

