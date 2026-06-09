import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "clinical_trials.db"
EXPORT_DIR = Path(__file__).parent.parent / "data" / "exports"

# Columns that store JSON-encoded strings — parse them into real objects on export.
JSON_COLUMNS = {
    "studies": {"conditions", "condition_keywords", "interventions", "arm_groups", "locations", "primary_outcomes", "secondary_outcomes"},
    "sources": {"target_evidence_types"},
}


def _connect_readonly() -> sqlite3.Connection:
    uri = DB_PATH.as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_json_fields(row: dict, table: str) -> dict:
    json_cols = JSON_COLUMNS.get(table, set())
    for col in json_cols:
        if col in row and isinstance(row[col], str):
            try:
                row[col] = json.loads(row[col])
            except (json.JSONDecodeError, TypeError):
                pass
    return row


def _get_all_tables(conn: sqlite3.Connection) -> list[str]:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]


def _export_table(conn: sqlite3.Connection, table: str) -> list[dict]:
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    return [_parse_json_fields(dict(row), table) for row in rows]


def export_all(output_dir: Path = EXPORT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    conn = _connect_readonly()

    try:
        tables = _get_all_tables(conn)
        print(f"[export] found {len(tables)} tables: {', '.join(tables)}")

        for table in tables:
            rows = _export_table(conn, table)
            out_path = output_dir / f"{table}.json"
            with open(out_path, "w") as f:
                json.dump(rows, f, indent=2, default=str)
            print(f"[export] {table}: {len(rows)} rows -> {out_path}")

    finally:
        conn.close()

    print(f"\n[export] done. files written to {output_dir.resolve()}")


if __name__ == "__main__":
    export_all()
