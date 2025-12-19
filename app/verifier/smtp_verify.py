# backend/app/verifier/smtp_verify.py

import smtplib
import socket
import time
import random
import string
from dataclasses import dataclass


# ------------------------------------------------------------
# Result object (compatible con verify_engine y worker_full)
# ------------------------------------------------------------
@dataclass
class SMTPVerifyResult:
    smtp_status: str            # deliverable / invalid / unknown
    code: int
    message: str
    mx_host: str
    is_catch_all: bool
    anti_spam: bool
    greylisted: bool
    duration_ms: int
    server_banner: str = None


# ------------------------------------------------------------
# Dominios que NO permiten verificación por diseño
# ------------------------------------------------------------
NON_VERIFIABLE_DOMAINS = {
    "gmail.com", "googlemail.com",
    "outlook.com", "hotmail.com", "live.com",
    "yahoo.com",
    "icloud.com", "me.com", "mac.com",
    "office365.com", "microsoft.com",
}


def _random_address(domain: str) -> str:
    rand = ''.join(random.choices(string.ascii_lowercase, k=12))
    return f"{rand}@{domain}"


# ------------------------------------------------------------
# SMTP VERIFICATION estable y profesional
# ------------------------------------------------------------
def smtp_verify(email: str, mx_host: str, timeout=4) -> SMTPVerifyResult:
    start = time.time()
    domain = email.split("@")[1]

    # 1. Dominios que no exponen RCPT verification → unknown
    if domain in NON_VERIFIABLE_DOMAINS:
        return SMTPVerifyResult(
            smtp_status="unknown",
            code=0,
            message="Domain does not support SMTP verification (privacy protected).",
            mx_host=mx_host,
            is_catch_all=False,
            anti_spam=False,
            greylisted=False,
            duration_ms=int((time.time() - start) * 1000)
        )

    # 2. No MX → invalid
    if not mx_host:
        return SMTPVerifyResult(
            smtp_status="invalid",
            code=0,
            message="No MX records available.",
            mx_host="",
            is_catch_all=False,
            anti_spam=False,
            greylisted=False,
            duration_ms=int((time.time() - start) * 1000)
        )

    ports = [25, 587, 465]
    last_error = ""
    server_banner = None

    for port in ports:
        server = None
        try:
            # -------------------------------
            # Conexión a servidor SMTP
            # -------------------------------
            if port == 465:
                server = smtplib.SMTP_SSL(mx_host, port, timeout=timeout)
            else:
                server = smtplib.SMTP(mx_host, port, timeout=timeout)

            # Banner
            banner = server.docmd("EHLO")
            server_banner = banner[1].decode(errors="ignore") if isinstance(banner[1], bytes) else str(banner[1])

            # STARTTLS para 587 si soporta
            if port == 587:
                try:
                    server.starttls()
                    server.ehlo()
                except Exception:
                    pass

            # MAIL FROM
            mf_code, mf_msg = server.mail("verify@checker.com")

            if mf_code >= 400:
                # No se puede verificar → servidor bloquea RCPT
                return SMTPVerifyResult(
                    smtp_status="unknown",
                    code=mf_code,
                    message="Server rejected MAIL FROM (anti-spam).",
                    mx_host=mx_host,
                    is_catch_all=False,
                    anti_spam=True,
                    greylisted=False,
                    duration_ms=int((time.time() - start) * 1000),
                    server_banner=server_banner
                )

            # RCPT TO: email real
            code, msg = server.rcpt(email)
            msg = msg.decode() if isinstance(msg, bytes) else str(msg)

            # -------------------------------
            # Catch-all test (seguro)
            # -------------------------------
            fake_email = _random_address(domain)
            fake_code, _ = server.rcpt(fake_email)

            is_catch = (200 <= fake_code < 300)

            # -------------------------------
            # Clasificación de status
            # -------------------------------
            if 200 <= code < 300:
                status = "deliverable"
            elif code in (450, 451, 452):
                status = "unknown"      # greylisting / temp fail
            elif code in (550, 551, 553):
                status = "invalid"
            else:
                status = "unknown"

            # -------------------------------
            # Anti-spam heuristics
            # -------------------------------
            is_anti_spam = any(x in server_banner for x in [
                "Proofpoint", "Barracuda", "Google Frontend", "Spamhaus"
            ])

            return SMTPVerifyResult(
                smtp_status=status,
                code=code,
                message=msg,
                mx_host=mx_host,
                is_catch_all=is_catch,
                anti_spam=is_anti_spam,
                greylisted=(code in (450, 451)),
                duration_ms=int((time.time() - start) * 1000),
                server_banner=server_banner
            )

        except (socket.timeout, socket.error, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
            last_error = str(e)
            continue

        finally:
            try:
                if server:
                    server.quit()
            except:
                pass

    # Si NINGÚN puerto respondió
    return SMTPVerifyResult(
        smtp_status="unknown",
        code=0,
        message=last_error,
        mx_host=mx_host,
        is_catch_all=False,
        anti_spam=False,
        greylisted=False,
        duration_ms=int((time.time() - start) * 1000),
        server_banner=server_banner
    )


