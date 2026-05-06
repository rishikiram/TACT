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
    phase               TEXT,
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
    print(f"[db] initialized at {DB_PATH}")


def upsert_study(conn: sqlite3.Connection, study: dict) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO studies (
            nct_id, title, status, phase, study_type,
            start_date, completion_date,
            sponsor, sponsor_class,
            conditions, condition_keywords,
            interventions, arm_groups,
            enrollment, enrollment_type,
            masking, allocation, intervention_model, primary_purpose,
            locations, ingested_at
        ) VALUES (
            :nct_id, :title, :status, :phase, :study_type,
            :start_date, :completion_date,
            :sponsor, :sponsor_class,
            :conditions, :condition_keywords,
            :interventions, :arm_groups,
            :enrollment, :enrollment_type,
            :masking, :allocation, :intervention_model, :primary_purpose,
            :locations, :ingested_at
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
