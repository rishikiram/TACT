import os
from contextlib import contextmanager
import psycopg

@contextmanager
def connect_aact():
    conn = psycopg.connect(
        host="aact-db.ctti-clinicaltrials.org",
        port=5432,
        dbname="aact",
        user=os.environ["AACT_USER"],
        password=os.environ["AACT_PASSWORD"],
    )
    try:
        yield conn
    finally:
        conn.close()
