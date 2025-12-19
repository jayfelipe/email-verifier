"""
smtp_verify.py
Verificación SMTP para una dirección de correo sobre un registro MX dado.

API principal:
    smtp_verify(email, mx_record, *,
                helo_host="verifier.local",
                from_address="verifier@yourdomain.com",
                timeout=10.0,
                max_retries=3,
                ports=(25, 465),
                starttls_preference=True,
                check_catch_all_count=1)

Retorna un SMTPVerifyResult (dataclass) con detalles y metadatos.
"""

import smtplib
import socket
import ssl
import time
import random
import string
from dataclasses import dataclass, asdict
from typing import Optional, List, Tuple, Union

# -------------------------
# Dataclasses de salida
# -------------------------
@dataclass
class SMTPAttempt:
    host: str
    port: int
    starttls: bool
    helo: str
    success: bool
    smtp_code: Optional[int] = None
    smtp_message: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    raw: Optional[str] = None

@dataclass
class SMTPVerifyResult:
    email: str
    domain: str
    mx_host: str
    is_valid: Optional[bool]  # True = accepted; False = rejected; None = unknown/ambiguous
    smtp_code: Optional[int]
    smtp_message: Optional[str]
    is_catch_all: Optional[bool]
    temp_error: bool
    attempts: List[SMTPAttempt]
    warnings: List[str]
    duration: float

# -------------------------
# Helpers
# -------------------------
def _random_localpart(length: int = 12) -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# Internal function: try one SMTP session and return (code, message, raw)
def _smtp_session_check(mx_host: str,
                        port: int,
                        target_rcpt: str,
                        from_address: str,
                        helo_host: str,
                        timeout: float,
                        use_starttls: bool) -> Tuple[int, str, str]:
    """
    Conecta al servidor MX, hace EHLO/HELO, MAIL FROM y RCPT TO (no DATA).
    Retorna (code, message, raw_text).
    Lanza excepciones en errores de conexión/timeout.
    """
    # Configure basic SSL context
    context = ssl.create_default_context()
    start_time = time.time()
    raw_trace = []
    # Use smtplib SMTP or SMTP_SSL depending on port
    if port == 465:
        # SSL wrapped
        server = smtplib.SMTP_SSL(timeout=timeout, host=mx_host, port=port, context=context)
    else:
        server = smtplib.SMTP(host=mx_host, port=port, timeout=timeout)

    try:
        # server.set_debuglevel(1)  # útil para debugging
        code = None
        msg = ""
        # 1) Initial greet (connect done by constructor)
        # 2) EHLO/HELO
        try:
            code_ehlo, resp_ehlo = server.ehlo(name=helo_host)
            raw_trace.append(f"EHLO -> {code_ehlo} {resp_ehlo!r}")
        except smtplib.SMTPHeloError:
            # Fallback to HELO
            code_he, resp_he = server.helo(name=helo_host)
            raw_trace.append(f"HELO -> {code_he} {resp_he!r}")

        # 3) STARTTLS if supported and requested and not SSL socket already
        if use_starttls and port != 465:
            # check extensions to see if STARTTLS is announced
            if server.has_extn('starttls'):
                server.starttls(context=context)
                # After STARTTLS need to EHLO again
                server.ehlo(name=helo_host)
                raw_trace.append("STARTTLS executed and EHLO again")
            else:
                raw_trace.append("STARTTLS not offered by server")

        # 4) MAIL FROM
        code_mail, resp_mail = server.mail(from_address)
        raw_trace.append(f"MAIL FROM -> {code_mail} {resp_mail!r}")

        # 5) RCPT TO (target)
        code_rcpt, resp_rcpt = server.rcpt(target_rcpt)
        raw_trace.append(f"RCPT TO {target_rcpt} -> {code_rcpt} {resp_rcpt!r}")

        code = int(code_rcpt) if code_rcpt is not None else None
        # resp_rcpt may be bytes or str
        msg = resp_rcpt.decode('utf-8', errors='ignore') if isinstance(resp_rcpt, (bytes, bytearray)) else str(resp_rcpt)

        # Always quit politely
        try:
            server.quit()
        except Exception:
            # some servers close connection abruptly; ignore
            pass

        duration = time.time() - start_time
        return code, msg, "\n".join(raw_trace)
    finally:
        try:
            server.close()
        except Exception:
            pass

# -------------------------
# API principal
# -------------------------
def smtp_verify(email: str,
                mx_record: Union[str, Tuple[int, str]],
                *,
                helo_host: str = "verifier.local",
                from_address: str = "verifier@yourdomain.com",
                timeout: float = 10.0,
                max_retries: int = 3,
                ports: Tuple[int, ...] = (25, 465),
                starttls_preference: bool = True,
                check_catch_all_count: int = 1) -> SMTPVerifyResult:
    """
    Verifica email con servidor MX (mx_record puede ser 'mx.host.tld' o (pref, 'mx.host.tld')).
    - check_catch_all_count: número de pruebas aleatorias para detectar catch-all (0 para deshabilitar).
    """
    t0 = time.time()
    warnings = []
    attempts: List[SMTPAttempt] = []

    domain = email.split("@", 1)[1].lower() if "@" in email else ""
    # normalize mx_host
    if isinstance(mx_record, (tuple, list)):
        mx_host = str(mx_record[1])
    else:
        mx_host = str(mx_record)

    # Ensure helo_host doesn't contain brackets etc.
    helo = helo_host

    # Retry loop with exponential backoff for transient errors (connection, timeout, 4xx)
    last_code = None
    last_msg = None
    temp_error_flag = False
    final_is_valid = None

    for attempt in range(1, max_retries + 1):
        backoff = (2 ** (attempt - 1)) + random.random() * 0.1
        for port in ports:
            try:
                start = time.time()
                use_starttls = starttls_preference
                code, msg, raw = _smtp_session_check(mx_host=mx_host,
                                                     port=port,
                                                     target_rcpt=email,
                                                     from_address=from_address,
                                                     helo_host=helo,
                                                     timeout=timeout,
                                                     use_starttls=use_starttls)
                duration = time.time() - start
                success = (code is not None and 200 <= code < 400)
                att = SMTPAttempt(host=mx_host, port=port, starttls=use_starttls, helo=helo,
                                  success=success, smtp_code=code, smtp_message=msg,
                                  duration=duration, raw=raw)
                attempts.append(att)
                last_code = code
                last_msg = msg

                # Interpret codes
                if code is None:
                    # Unknown outcome (ambiguous)
                    temp_error_flag = True
                    warnings.append("Código SMTP no obtenido")
                elif 200 <= code < 300 or code == 250:
                    # Accepted — but could be catch-all or privacy-protecting server
                    final_is_valid = True
                    temp_error_flag = False
                    # We can stop trying ports/retries here
                    break
                elif 400 <= code < 500:
                    # Transient error (greylisting / temp)
                    temp_error_flag = True
                    warnings.append(f"Respuesta temporal {code}: {msg}")
                    # try next port or retry after backoff
                elif 500 <= code < 600:
                    # Permanent rejection (user unknown / mailbox unavailable)
                    final_is_valid = False
                    temp_error_flag = False
                    break
                else:
                    # Unexpected code: mark as temp
                    temp_error_flag = True
                    warnings.append(f"Respuesta SMTP inesperada {code}: {msg}")

            except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, smtplib.SMTPHeloError,
                    smtplib.SMTPResponseException, socket.timeout, ConnectionRefusedError, OSError) as e:
                errstr = str(e)
                attempts.append(SMTPAttempt(host=mx_host, port=port, starttls=starttls_preference, helo=helo,
                                            success=False, smtp_code=None, smtp_message=None,
                                            duration=None, error=errstr))
                temp_error_flag = True
                warnings.append(f"Conexión/SMTP error en intento {attempt} puerto {port}: {errstr}")
                # continue to next port or retry
            # end try port
        if final_is_valid is not None and not temp_error_flag:
            # tenemos decisión final (accept or reject)
            break
        # si temp_error_flag entonces backoff y retry
        time.sleep(backoff)

    # Si aún no decidimos y tenemos códigos de intento, inferir a partir del último código
    if final_is_valid is None:
        if last_code is not None:
            if 200 <= last_code < 300:
                final_is_valid = True
            elif 400 <= last_code < 500:
                final_is_valid = None
                temp_error_flag = True
            elif 500 <= last_code < 600:
                final_is_valid = False
        else:
            # Sin datos: ambiguous
            final_is_valid = None
            warnings.append("Sin respuesta SMTP concluyente")

    # ----- Detectar catch-all si aplica -----
    is_catch_all = None
    if check_catch_all_count and final_is_valid is True:
        # Hacer pruebas con direcciones aleatorias en el mismo dominio
        accept_count = 0
        total_checks = max(1, check_catch_all_count)
        for i in range(total_checks):
            random_local = f"noexist_{_random_localpart(10)}"
            random_addr = f"{random_local}@{domain}"
            try:
                # nueva sesión por prueba para evitar caching
                code_r, msg_r, raw_r = _smtp_session_check(mx_host=mx_host,
                                                           port=ports[0] if ports else 25,
                                                           target_rcpt=random_addr,
                                                           from_address=from_address,
                                                           helo_host=helo,
                                                           timeout=timeout,
                                                           use_starttls=starttls_preference)
                if code_r is not None and 200 <= code_r < 300:
                    accept_count += 1
            except Exception as e:
                warnings.append(f"Error durante prueba catch-all: {e}")
        # heurística: si la mayoría acepta -> probable catch-all
        is_catch_all = (accept_count == total_checks)
        if is_catch_all:
            warnings.append("Dominio parece aceptar direcciones arbitrarias (catch-all)")

    duration_total = time.time() - t0
    result = SMTPVerifyResult(
        email=email,
        domain=domain,
        mx_host=mx_host,
        is_valid=final_is_valid,
        smtp_code=last_code,
        smtp_message=last_msg,
        is_catch_all=is_catch_all,
        temp_error=temp_error_flag,
        attempts=attempts,
        warnings=warnings,
        duration=duration_total
    )
    return result

# -------------------------
# Ejemplo de uso
# -------------------------
if __name__ == "__main__":
    # Ejemplos — ATENCIÓN: ejecutar múltiples verificaciones puede causar tráfico saliente importante.
    examples = [
        ("example.user@gmail.com", "alt1.gmail-smtp-in.l.google.com"),
        ("noexist-123456@some-small-domain.test", "mx.somedomain.test"),
    ]

    for email, mx in examples:
        print("Verificando:", email, "on MX:", mx)
        res = smtp_verify(email, mx, helo_host="verifier.yourdomain.com",
                          from_address="verifier@yourdomain.com", timeout=8.0,
                          max_retries=2, ports=(25, 465), starttls_preference=True,
                          check_catch_all_count=1)
        print("Resultado:", asdict(res))
        print("----\n")
