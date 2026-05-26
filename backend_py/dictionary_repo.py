"""
All SQL operations against the DataDictionary table.
Uses abstract connection, which can be swapped for something else like a PostgreSQL connection.
See DIALECT NOTEs for sqlite specific sql code.
"""

from db import DATA_DICTIONARY_SCHEMA, get_table_columns


def ensure_table(conn) -> None:
    """Create the DataDictionary table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute(DATA_DICTIONARY_SCHEMA)


def build_from_table(conn, table_name: str = "studies") -> int:
    """
    Replace all DataDictionary rows for table_name with a fresh set derived
    from the current schema. Any existing annotations are wiped.
    Returns the number of columns registered.

    DIALECT NOTE: placeholder ? is SQLite/DB-API style.
    """
    cols = get_table_columns(conn, table_name)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM DataDictionary WHERE table_name = ?", (table_name,))
    cursor.executemany(
        "INSERT INTO DataDictionary (table_name, column_name) VALUES (?, ?)",
        [(table_name, col["name"]) for col in cols],
    )
    return len(cols)


def get_annotations(conn, table_name: str) -> dict[str, dict]:
    """
    Returns {column_name: {source, derivation, plain_description}}
    for all rows matching table_name. Pure ANSI SQL — no dialect changes needed.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT column_name, source, derivation, plain_description "
        "FROM DataDictionary WHERE table_name = ?",
        (table_name,),
    )
    rows = cursor.fetchall()
    return {r["column_name"]: dict(r) for r in rows}
