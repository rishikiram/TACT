import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "clinical_trials.db"

# Schema for the DataDictionary annotations table.
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

TABLES_SCHEMA = """
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

CREATE TABLE IF NOT EXIST sources (
    source_id               INTEGER PRIMARY KEY,
    type                    TEXT,
    title                   TEXT,
    url                     TEXT
);

CREATE TABLE IF NOT EXISTS evidence_objects (
    evidence_object_id      INTEGER PRIMARY KEY,
    type                    TEXT, -- could be turned into a fk with a set of options
    statement               TEXT, 
    normalized_value        TEXT,
    confidence              TEXT -- could also be turned into a fk with a set of options
);

CREATE TABLE IF NOT EXIST claims (
    claim_id                INTEGER PRIMARY KEY,
    statement               TEXT,
    status                  TEXT, -- could be a fk enum, also could be renamed to 'veracity' or confidence
    risk_note               TEXT
);

CREATE TABLE IF NOT EXIST requirements (
    requirement_id          INTEGER PRIMARY KEY,
    jurisdiction            TEXT,
    domain                  TEXT, -- could be fk enum
    expectation             TEXT
);

CREATE TABLE IF NOT EXIST gaps (
    gap_id                  INTEGER PRIMARY KEY,
    type                    TEXT,
    severity                TEXT,
    jurisdiction            TEXT,
    recommended_action      TEXT
);
"""




def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # row_factory enables dict-like row access. PostgreSQL equivalent: psycopg2.extras.RealDictCursor
    conn.row_factory = sqlite3.Row
    # DIALECT NOTE: PRAGMA is SQLite-specific. Remove for PostgreSQL.
    conn.cursor().execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(SCHEMA)
        # DIALECT NOTE: pragma_table_info is SQLite-specific.
        cols = [row[0] for row in cursor.execute("SELECT name FROM pragma_table_info('studies')").fetchall()]
        lines = SCHEMA.strip().splitlines()
        lines = lines[1:-1]  # skip CREATE TABLE and closing );
        for line in lines:
            if line.strip() and not line.strip().startswith("--"):
                col_def = line.strip().split(",")[0]
                col_name = col_def.split()[0]
                if col_name not in cols:
                    print(f"[db] adding missing column: {col_name}")
                    cursor.execute(f"ALTER TABLE studies ADD COLUMN {col_def};")
    print(f"[db] initialized at {DB_PATH}")

def init_tables() -> None:
    pass

def init_relationships() -> None:
    pass

def init_relationship_contraints() -> None:
    pass


def upsert_study(conn: sqlite3.Connection, study: dict) -> None:
    conn.cursor().execute(
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
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()


def count() -> int:
    return query("SELECT COUNT(*) FROM studies")[0][0]


def get_table_columns(conn, table_name: str) -> list[dict]:
    """
    Returns [{name, type, notnull}, ...] for each column in table_name.

    DIALECT NOTE: uses SQLite PRAGMA table_info.
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    rows = cursor.fetchall()
    return [{"name": r["name"], "type": r["type"], "notnull": bool(r["notnull"])} for r in rows]


def build_data_dictionary(table_name: str = "studies") -> None:
    """
    Bootstrap entry point. Creates the DataDictionary table if needed, then
    replaces all rows for table_name with the current schema — existing annotations
    are wiped. Delegates all SQL to dictionary_repo so this function needs no changes
    when switching databases (only connect() and get_table_columns() above change).
    """
    from dictionary_repo import ensure_table, build_from_table
    with connect() as conn:
        ensure_table(conn)
        n = build_from_table(conn, table_name)
    print(f"[db] DataDictionary built for '{table_name}' — {n} columns registered")

