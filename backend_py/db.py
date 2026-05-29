import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "clinical_trials.db"


TABLES_SCHEMA = """
CREATE TABLE studies (
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

CREATE TABLE sources (
    source_id               INTEGER PRIMARY KEY,
    type                    TEXT,
    title                   TEXT,
    url                     TEXT
);

CREATE TABLE evidence_objects (
    evidence_object_id      INTEGER PRIMARY KEY,
    type                    TEXT, -- could be turned into a fk with a set of options
    statement               TEXT, 
    normalized_value        TEXT,
    confidence              TEXT -- could also be turned into a fk with a set of options
);

CREATE TABLE claims (
    claim_id                INTEGER PRIMARY KEY,
    statement               TEXT,
    status                  TEXT, -- could be a fk enum, also could be renamed to 'veracity' or confidence
    risk_note               TEXT
);

CREATE TABLE requirements (
    requirement_id          INTEGER PRIMARY KEY,
    jurisdiction            TEXT,
    domain                  TEXT, -- could be fk enum
    expectation             TEXT
);

CREATE TABLE gaps (
    gap_id                  INTEGER PRIMARY KEY,
    type                    TEXT,
    severity                TEXT,
    jurisdiction            TEXT,
    recommended_action      TEXT
);
"""

RELATIONSHIPS_SCHEMA = """
-- Many-to-many sources to evidence  -- this might be unecessary, could be one-to-many (source-to-EOs)
CREATE TABLE evidence_object_sources (
    source_id               INTEGER,
    evidence_object_id      INTEGER,
    PRIMARY KEY (source_id, evidence_object_id),
);
ALTER TABLE evidence_object_sources(
    CONSTRAINT fk__source_id__EO_src
    FOREIGN KEY (source_id)
    REFERENCES sources(source_id)
);
ALTER TABLE evidence_object_sources(
    CONSTRAINT fk__EO_id__EO_src
    FOREIGN KEY (evidence_object_id)
    REFERENCES evidence_objects(evidence_object_id)
);

-- Many-to-many evidence to claims
CREATE TABLE claim_evidence_objects (
    claim_id                INTEGER,
    evidence_object_id      INTEGER,
    PRIMARY KEY (claim_id, evidence_object_id)
);
ALTER TABLE claim_evidence_objects(
    CONSTRAINT fk__claim_id__claim_EO
    FOREIGN KEY (claim_id)
    REFERENCES claims(claim_id)
);
ALTER TABLE claim_evidence_objects(
    CONSTRAINT fk__EOid__claim_EO
    FOREIGN KEY (evidence_object_id)
    REFERENCES evidence_objects(evidence_object_id)
);

-- Many-to-many-to-many claims and requirements to gaps
CREATE requirement_claim_gaps (
    claim_id                INTEGER,
    requirement_id          INTEGER,
    gap_id                  INTEGER,
    PRIMARY KEY (claim_id, requirement_id, gap_id)
);
ALTER TABLE requirement_claim_gaps(
    CONSTRAINT fk__claim_id__claim_req_gap
    FOREIGN KEY (claim_id)
    REFERENCES claims(claim_id)
);
ALTER TABLE requirement_claim_gaps(
    CONSTRAINT fk__requirement_id__claim_req_gap
    FOREIGN KEY (requirement_id)
    REFERENCES requirements(requirement_id)
);
ALTER TABLE requirement_claim_gaps(
    CONSTRAINT fk__gap_id__claim_req_gap
    FOREIGN KEY (gap_id)
    REFERENCES gaps(gap_id)
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
        cursor.execute(TABLES_SCHEMA)
        cursor.execute(RELATIONSHIPS_SCHEMA)
    print(f"[db] initialized at {DB_PATH}")

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
        conn.commit()
    return len(studies)

def insert_sources(sources: list[dict]) -> int:
    # TODO: shift pk generation to RDBM, and enable row replacment
    with connect() as conn:
        crsr = conn.cursor()
        for source in sources:
            crsr.execute(
                """
                INSERT OR REPLACE INTO sources (
                    source_id, type, title, url
                ) VALUES (
                    :source_id, :type, :title, :url
                )
                """,
                source
            )
        conn.commit()
    return len(sources)

def insert_and_link_EOs(evidence_objs) -> int:
    # TODO: shift pk generation to RDBM, and enable row replacment
    with connect() as conn:
        crsr = conn.cursor()
        for eo in evidence_objs:
            crsr.execute(
                """
                INSERT OR REPLACE INTO evidence_objects (
                    evidence_object_id, type, statement
                    normalized_value, confidence
                ) VALUES (
                    :evidence_object_id, :type, :statement
                    :normalized_value, :confidence
                )
                """
            )
        for 
    return -1

def insert_and_link_claims(claims) -> int:
    return -1

def insert_requirements(requirements) -> int:
    return -1

def insert_and_link_gaps(gaps) -> int:
    return -1

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
    from backend_py.data_dictionary import build_dataDictionary, build_from_table
    with connect() as conn:
        build_dataDictionary(conn)
        n = build_from_table(conn, table_name)
    print(f"[db] DataDictionary built for '{table_name}' — {n} columns registered")

