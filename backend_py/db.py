import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "clinical_trials.db"

# Schema for the DataDictionary annotations table.
# To migrate to PostgreSQL: change TEXT -> VARCHAR/TEXT (compatible),
# PRIMARY KEY syntax is identical.
DATA_DICTIONARY_SCHEMA = """
CREATE TABLE IF NOT EXISTS DataDictionary (
    table_name        TEXT NOT NULL,
    column_name       TEXT NOT NULL,
    source            TEXT NOT NULL DEFAULT '',
    derivation        TEXT NOT NULL DEFAULT '',
    plain_description TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (table_name, column_name)
);
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS studies (
    nct_id                  TEXT PRIMARY KEY,
    title                   TEXT,
    status                  TEXT,
    phase1                  BOOLEAN,
    phase2                  BOOLEAN,
    phase3                  BOOLEAN,
    phase4                  BOOLEAN,
    phase_text              TEXT,
    study_type              TEXT,
    start_date              TEXT,
    start_date_type         TEXT,
    primary_completion_date TEXT,
    primary_completion_date_type TEXT,
    completion_date         TEXT,
    completion_date_type    TEXT,
    last_update_post        TEXT,
    sponsor                 TEXT,
    sponsor_class           TEXT,
    conditions              TEXT,   -- JSON array
    condition_keywords      TEXT,   -- JSON array
    interventions           TEXT,   -- JSON array
    arm_groups              TEXT,   -- JSON array
    enrollment              INTEGER,
    enrollment_type         TEXT,
    masking                 TEXT,
    allocation              TEXT,
    intervention_model      TEXT,
    primary_purpose         TEXT,
    locations               TEXT,   -- JSON array of {facility, city, state, country, lat, lon}
    primary_outcomes        TEXT,   -- JSON array
    secondary_outcomes      TEXT,   -- JSON array
    ingested_at             TEXT
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # safe for concurrent readers
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        cols = [row[0] for row in conn.execute("SELECT name FROM pragma_table_info('studies')").fetchall()]
        # print(f"[db] columns: {cols}")
        # add new columns if schema has changed, based on SCHEMA text
        lines = SCHEMA.strip().splitlines()
        lines = lines[1:-1]  # skip CREATE TABLE and closing );
        for line in lines:
            if line.strip() and not line.strip().startswith("--"):
                col_def = line.strip().split(",")[0]  # get column definition before comma
                col_name = col_def.split()[0]
                if col_name not in cols:
                    print(f"[db] adding missing column: {col_name}")
                    conn.execute(f"ALTER TABLE studies ADD COLUMN {col_def};")
    print(f"[db] initialized at {DB_PATH}")


def upsert_study(conn: sqlite3.Connection, study: dict) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO studies (
            nct_id, title, status, phase1, phase2, phase3, phase4, phase_text, study_type,
            start_date, start_date_type, primary_completion_date, primary_completion_date_type,
            completion_date, completion_date_type, last_update_post,
            sponsor, sponsor_class,
            conditions, condition_keywords,
            interventions, arm_groups,
            enrollment, enrollment_type,
            masking, allocation, intervention_model, primary_purpose,
            locations, primary_outcomes, secondary_outcomes, ingested_at
        ) VALUES (
            :nct_id, :title, :status, :phase1, :phase2, :phase3, :phase4, :phase_text, :study_type,
            :start_date, :start_date_type, :primary_completion_date, :primary_completion_date_type,
            :completion_date, :completion_date_type, :last_update_post,
            :sponsor, :sponsor_class,
            :conditions, :condition_keywords,
            :interventions, :arm_groups,
            :enrollment, :enrollment_type,
            :masking, :allocation, :intervention_model, :primary_purpose,
            :locations, :primary_outcomes, :secondary_outcomes, :ingested_at
        )
        """,
        study,
    )


def upsert_studies(studies: list[dict]) -> int:
    with connect() as conn:
        for study in studies:
            upsert_study(conn, study)
    return len(studies)


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


def count() -> int:
    return query("SELECT COUNT(*) FROM studies")[0][0]


def get_table_columns(conn, table_name: str) -> list[dict]:
    """
    Returns [{name, type, notnull}, ...] for each column in table_name.

    DIALECT NOTE: uses SQLite PRAGMA table_info.
    PostgreSQL replacement:
        SELECT column_name AS name, data_type AS type,
               (is_nullable = 'NO') AS notnull
        FROM information_schema.columns
        WHERE table_name = %s ORDER BY ordinal_position
    Also update placeholder from ? to %s throughout this file and dictionary_repo.py.
    """
    rows = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    return [{"name": r["name"], "type": r["type"], "notnull": bool(r["notnull"])} for r in rows]


def build_data_dictionary(table_name: str = "studies") -> None:
    """
    Bootstrap entry point. Creates the DataDictionary table and registers
    all columns from table_name. Safe to re-run — existing rows are untouched.
    Delegates all SQL to dictionary_repo so this function needs no changes
    when switching databases (only connect() and get_table_columns() above change).
    """
    from dictionary_repo import ensure_table, build_from_table
    with connect() as conn:
        ensure_table(conn)
        n = build_from_table(conn, table_name)
    print(f"[db] DataDictionary built for '{table_name}' — {n} columns registered")
