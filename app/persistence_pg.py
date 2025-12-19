import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/verifier")

@contextmanager
def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()

def insert_verification(record: dict):
    """
    record must contain: email, domain, job_id, duration_seconds, dns, smtp, heuristics, scoring, status
    """
    sql = """
    INSERT INTO email_verifications (email, domain, job_id, duration_seconds, dns, smtp, heuristics, scoring, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id, created_at
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (
                record.get("email"),
                record.get("domain"),
                record.get("job_id"),
                record.get("duration_seconds"),
                psycopg2.extras.Json(record.get("dns")),
                psycopg2.extras.Json(record.get("smtp")),
                psycopg2.extras.Json(record.get("heuristics")),
                psycopg2.extras.Json(record.get("scoring")),
                record.get("status")
            ))
            conn.commit()
            return cur.fetchone()
