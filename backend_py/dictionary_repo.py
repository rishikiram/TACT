"""
All SQL operations against the DataDictionary table.
Uses abstract connection, which can be swapped for something else like a PostgreSQL connection.
See DIALECT NOTEs for sqlite specific sql code.
"""

from pathlib import Path
from db import DATA_DICTIONARY_SCHEMA, get_table_columns

ANNOTATIONS_YAML = Path(__file__).parent / "column_annotations.yaml"


def ensure_table(conn) -> None:
    """Create the DataDictionary table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute(DATA_DICTIONARY_SCHEMA)


def build_from_table(conn, table_name: str = "studies") -> int:
    """
    Replace all DataDictionary rows for table_name with a fresh set derived
    from the current schema. Any existing annotations are wiped. Include 
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
    updated = load_annotations_from_yaml(conn, table_name, ANNOTATIONS_YAML)
    if not updated == len(cols):
        print("Not all data fields have metadata written in column_annotations.yaml...")
    return len(cols)


def load_annotations_from_yaml(conn, table_name: str = "studies", yaml_path: Path = ANNOTATIONS_YAML) -> int:
    """
    Read column_annotations.yaml and UPDATE matching rows in DataDictionary.
    Rows must already exist (run build_from_table first).
    Returns the number of rows updated.

    DIALECT NOTE: placeholder ? is SQLite/DB-API style. Use %s for psycopg2.
    """
    import yaml
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    cursor = conn.cursor()
    updated = 0
    for column_name, ann in data.items():
        cursor.execute(
            """
            UPDATE DataDictionary
            SET source = ?, derivation = ?, plain_description = ?
            WHERE table_name = ? AND column_name = ?
            """,
            (
                ann.get("source", ""),
                ann.get("derivation", ""),
                ann.get("plain_description", ""),
                table_name,
                column_name,
            ),
        )
        updated += cursor.rowcount
    return updated


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
