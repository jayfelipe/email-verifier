from .smtp_pool import SMTPPool
import time

smtp_pool = SMTPPool(max_per_host=5, idle_timeout=60)

def batch_rcpt_check(from_address: str, mx_host: str, emails: list, port=25, use_ssl=False, helo_host="verifier.local", timeout=10):
    """
    Ejecuta MAIL FROM una vez y múltiples RCPT TO para la lista de emails (emails must belong to same domain).
    Devuelve dict email -> (code, message)
    """
    results = {}
    with smtp_pool.get_connection(host=mx_host, port=port, use_ssl=use_ssl, timeout=timeout, helo_host=helo_host) as conn:
        # try starttls
        try:
            conn.starttls_if_supported()
        except Exception:
            pass
        # MAIL FROM
        try:
            code_mail, resp_mail = conn.mail_from(from_address)
        except Exception as e:
            # connection issue: mark all as error
            for eaddr in emails:
                results[eaddr] = (None, f"mail_from_error: {e}")
            return results

        # For each recipient, do RCPT
        for rcpt in emails:
            try:
                code_rcpt, resp_rcpt = conn.rcpt(rcpt)
                # normalize message to str
                msg = resp_rcpt.decode('utf-8', errors='ignore') if isinstance(resp_rcpt, (bytes, bytearray)) else str(resp_rcpt)
                results[rcpt] = (code_rcpt, msg)
            except Exception as ex:
                results[rcpt] = (None, f"rcpt_error: {ex}")
        return results
