# backend/app/verifier/dns_mx.py

import dns.resolver
import dns.exception
import dns.name
import logging

logger = logging.getLogger("dns_mx")


class MXRecord:
    def __init__(self, host: str, priority: int = 0):
        self.host = host
        self.priority = priority


class MXLookupError(Exception):
    pass


PARKING_KEYWORDS = [
    "example.com",
    "invalid",
    "parking",
    "localhost",
]


# ---------------------------------------------------------
# get_mx_records (tu función original, estandarizada)
# ---------------------------------------------------------
def get_mx_records(domain: str) -> list[MXRecord]:
    if not domain or "." not in domain:
        raise MXLookupError(f"Dominio inválido: {domain}")

    try:
        normalized = dns.name.from_text(domain).to_text()
        answers = dns.resolver.resolve(normalized, "MX", lifetime=4.0)

        mx_records = []
        for rdata in answers:
            mx_host = str(rdata.exchange).rstrip(".")
            priority = int(rdata.preference)
            mx_records.append(MXRecord(host=mx_host, priority=priority))

        # Ordenar por prioridad
        mx_records = sorted(mx_records, key=lambda x: x.priority)

        # Detectar MX basura / parking
        for record in mx_records:
            for parking in PARKING_KEYWORDS:
                if parking in record.host:
                    raise MXLookupError(f"MX sospechoso/parking: {record.host}")

        return mx_records

    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return []   # Dominio válido pero sin MX

    except dns.exception.Timeout:
        raise MXLookupError(f"Timeout consultando MX de {domain}")

    except Exception as e:
        raise MXLookupError(f"Error inesperado MX lookup: {e}")


# ---------------------------------------------------------
# resolve_mx — Wrapper estándar para verify_engine
# ---------------------------------------------------------
async def resolve_mx(domain: str) -> list[MXRecord]:
    """
    Wrapper async para mantener compatibilidad con verify_engine.
    """
    try:
        return get_mx_records(domain)
    except MXLookupError as e:
        logger.error(f"MX lookup error for {domain}: {e}")
        raise


