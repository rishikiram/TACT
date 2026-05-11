import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "clinical_trials.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS studies (
    nct_id              TEXT PRIMARY KEY,
    title               TEXT,
    status              TEXT,
    phase1              BOOLEAN,
    phase2              BOOLEAN,
    phase3              BOOLEAN,
    phase4              BOOLEAN,
    phase_text          TEXT,
    study_type          TEXT,
    start_date          TEXT,
    completion_date     TEXT,
    sponsor             TEXT,
    sponsor_class       TEXT,
    conditions          TEXT,   -- JSON array
    condition_keywords  TEXT,   -- JSON array
    interventions       TEXT,   -- JSON array
    arm_groups          TEXT,   -- JSON array
    enrollment          INTEGER,
    enrollment_type     TEXT,
    masking             TEXT,
    allocation          TEXT,
    intervention_model  TEXT,
    primary_purpose     TEXT,
    locations           TEXT,   -- JSON array of {facility, city, state, country, lat, lon}
    primary_outcomes    TEXT,   -- JSON array
    secondary_outcomes  TEXT,   -- JSON array
    ingested_at         TEXT
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
            start_date, completion_date,
            sponsor, sponsor_class,
            conditions, condition_keywords,
            interventions, arm_groups,
            enrollment, enrollment_type,
            masking, allocation, intervention_model, primary_purpose,
            locations, primary_outcomes, secondary_outcomes, ingested_at
        ) VALUES (
            :nct_id, :title, :status, :phase1, :phase2, :phase3, :phase4, :phase_text, :study_type,
            :start_date, :completion_date,
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
