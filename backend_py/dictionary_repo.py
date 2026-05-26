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
    Replace all DataDictionary rows for table_name with a fresh set derived
    from the current schema. Any existing annotations are wiped.
    Returns the number of columns registered.
    """
    cols = get_table_columns(conn, table_name)
    conn.execute("DELETE FROM DataDictionary WHERE table_name = ?", (table_name,))
    conn.executemany(
        "INSERT INTO DataDictionary (table_name, column_name) VALUES (?, ?)",
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
