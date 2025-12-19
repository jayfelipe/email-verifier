# backend/app/verifier/web_fingerprint.py

import requests
from bs4 import BeautifulSoup

TIMEOUT = 6
HEADERS = {
    "User-Agent": "Mozilla/5.0 (EmailVerifierBot/1.0)"
}

PARKING_KEYWORDS = [
    "domain for sale",
    "buy this domain",
    "coming soon",
    "under construction",
    "parked",
    "sedo",
    "godaddy",
    "namecheap",
    "hostgator"
]


def get_web_fingerprint(domain: str) -> dict:
    result = {
        "has_website": False,
        "http_status": None,
        "https": False,
        "title": None,
        "meta_description": None,
        "has_favicon": False,
        "is_empty": True,          # solo TRUE si es claramente parking
        "looks_legit": False       # 👈 NUEVO
    }

    urls = [
        f"https://{domain}",
        f"http://{domain}"
    ]

    for url in urls:
        try:
            resp = requests.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT,
                allow_redirects=True
            )

            result["http_status"] = resp.status_code

            if resp.status_code >= 400:
                continue

            result["has_website"] = True
            result["https"] = resp.url.startswith("https")

            soup = BeautifulSoup(resp.text, "html.parser")

            # Title
            title = soup.title.string.strip() if soup.title and soup.title.string else None
            result["title"] = title

            # Meta description
            desc = soup.find("meta", attrs={"name": "description"})
            if desc and desc.get("content"):
                result["meta_description"] = desc["content"].strip()

            # Favicon
            favicon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
            if favicon:
                result["has_favicon"] = True

            # Texto visible
            text = soup.get_text(" ", strip=True).lower()

            # Detectar parking REAL
            if any(keyword in text for keyword in PARKING_KEYWORDS):
                result["is_empty"] = True
                result["looks_legit"] = False
            else:
                # No es parking → aunque sea web simple
                result["is_empty"] = False
                result["looks_legit"] = True

            break

        except requests.RequestException:
            continue

    return result
