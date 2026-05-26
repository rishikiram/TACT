"""
All SQL operations against the DataDictionary table.

Accepts a connection object from the caller — no direct calls to connect() here.
This makes the database backend swappable: change connect() and get_table_columns()
in db.py, and update the two DIALECT NOTEs below for PostgreSQL syntax.
"""

from db import DATA_DICTIONARY_SCHEMA, get_table_columns


def ensure_table(conn) -> None:
    """Create the DataDictionary table if it doesn't exist."""
    conn.executescript(DATA_DICTIONARY_SCHEMA)


def build_from_table(conn, table_name: str = "studies") -> int:
    """
    Register one DataDictionary row per column in table_name.
    Idempotent — existing rows are left untouched so annotations are never lost.
    Returns the total number of columns in the table (not just newly inserted).

    DIALECT NOTE: INSERT OR IGNORE is SQLite syntax.
    PostgreSQL equivalent:
        INSERT INTO DataDictionary (table_name, column_name)
        VALUES (%s, %s)
        ON CONFLICT (table_name, column_name) DO NOTHING
    """
    cols = get_table_columns(conn, table_name)
    conn.executemany(
        "INSERT OR IGNORE INTO DataDictionary (table_name, column_name) VALUES (?, ?)",
        [(table_name, col["name"]) for col in cols],
    )
    return len(cols)


def get_annotations(conn, table_name: str) -> dict[str, dict]:
    """
    Returns {column_name: {source, derivation, plain_description}}
    for all rows matching table_name. Pure ANSI SQL — no dialect changes needed.
    """
    rows = conn.execute(
        "SELECT column_name, source, derivation, plain_description "
        "FROM DataDictionary WHERE table_name = ?",
        (table_name,),
    ).fetchall()
    return {r["column_name"]: dict(r) for r in rows}
