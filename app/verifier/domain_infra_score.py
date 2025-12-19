# backend/app/verifier/domain_infra_score.py

"""
Capa 3 – Scoring de Infraestructura del Dominio
---------------------------------------------
Convierte señales técnicas del dominio en un score cuantificable (0–100).

Este score NO decide por sí solo el resultado final del email.
Se usa como señal fuerte para:
- Subir o bajar confianza en catch-all
- Castigar dominios inventados
- Evitar falsos deliverable
"""

from typing import Dict

# --------------------------------------------------
# Configuración de pesos (ajustable)
# --------------------------------------------------

WEIGHTS = {
    "domain_age_old": 15,        # > 2 años
    "domain_age_mid": 8,         # 6 meses – 2 años
    "domain_age_new": -15,       # < 6 meses

    "has_spf": 10,
    "no_spf": -20,

    "has_dmarc": 10,
    "no_dmarc": -10,

    "web_active": 15,
    "web_none": -15,
    "web_parking": -30,

    "https": 5,
    "no_https": -5,
}

BASE_SCORE = 50

# --------------------------------------------------
# Scoring principal
# --------------------------------------------------

def score_domain_infra(infra: Dict) -> Dict:
    score = BASE_SCORE
    reasons = []

    age = infra.get("domain_age_days")

    # -------------------------------
    # Antigüedad del dominio
    # -------------------------------
    if isinstance(age, int):
        if age >= 730:
            score += WEIGHTS["domain_age_old"]
            reasons.append("Old domain")
        elif age >= 180:
            score += WEIGHTS["domain_age_mid"]
            reasons.append("Mid-age domain")
        else:
            score += WEIGHTS["domain_age_new"]
            reasons.append("New domain")

    # -------------------------------
    # SPF
    # -------------------------------
    if infra.get("has_spf"):
        score += WEIGHTS["has_spf"]
        reasons.append("SPF configured")
    else:
        score += WEIGHTS["no_spf"]
        reasons.append("No SPF")

    # -------------------------------
    # DMARC
    # -------------------------------
    if infra.get("has_dmarc"):
        score += WEIGHTS["has_dmarc"]
        reasons.append("DMARC configured")
    else:
        score += WEIGHTS["no_dmarc"]
        reasons.append("No DMARC")

    # -------------------------------
    # Web presence
    # -------------------------------
    web = infra.get("web_status")
    if web == "active":
        score += WEIGHTS["web_active"]
        reasons.append("Active website")
    elif web == "parking":
        score += WEIGHTS["web_parking"]
        reasons.append("Parking domain")
    else:
        score += WEIGHTS["web_none"]
        reasons.append("No website")

    # -------------------------------
    # HTTPS
    # -------------------------------
    if infra.get("https"):
        score += WEIGHTS["https"]
        reasons.append("HTTPS enabled")
    else:
        score += WEIGHTS["no_https"]
        reasons.append("No HTTPS")

    # Clamp
    score = max(0, min(100, score))

    return {
        "domain": infra.get("domain"),
        "infra_score": score,
        "infra_reasons": reasons,
    }
