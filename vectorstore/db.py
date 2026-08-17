"""PostgreSQL + pgvector database connection."""
import os

import psycopg2
from pgvector.psycopg2 import register_vector

_conn = None


def get_conn():
    global _conn
    if _conn is None or _conn.closed:
        dsn = os.getenv("DATABASE_URL", "postgresql://veeza:1234@localhost:5432/veeza")
        _conn = psycopg2.connect(dsn)
        register_vector(_conn)
    return _conn


def has_country_data(country: str) -> bool:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM visa_chunks WHERE country = %s", (country.lower(),))
        return cur.fetchone()[0] > 0
