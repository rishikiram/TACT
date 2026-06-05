import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "clinical_trials.db"

CLAIM_STATUS_ENUM: tuple = ("assumption", "unsupported", "partially supported", "supported")
allowed_claim_status = ", ".join(f"'{s}'" for s in CLAIM_STATUS_ENUM)
CLAIM_REVIEW_STATUS_ENUM: tuple = ("ai_draft", "needs_review", "accepted", "rejected", "revised")
allowed_claim_review_status = ", ".join(f"'{s}'" for s in CLAIM_REVIEW_STATUS_ENUM)

GAP_SEVERITY_ENUM: tuple = ("no data", "non-conclusive", "high", "medium", "low", "zero")
allowed_gaps = ", ".join(f"'{s}'" for s in GAP_SEVERITY_ENUM)

TABLES_SCHEMA = f"""
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
    locations               TEXT,   -- JSON array of [facility, city, state, country, lat, lon]
    primary_outcomes        TEXT,   -- JSON array
    secondary_outcomes      TEXT,   -- JSON array
    ingested_at             TEXT
);

CREATE TABLE IF NOT EXISTS sources (
    id                      INTEGER PRIMARY KEY,
    uid                     STRING UNIQUE,
    type                    TEXT,
    title                   TEXT,
    url                     TEXT,
    target_evidence_types   TEXT   -- JSON array for now -- this is how im imagining a user programaticaly allowing the repo to build the EOs
);

CREATE TABLE IF NOT EXIST queries (
    uid                     TEXT PRIMARY KEY,
    text                    TEXT
    -- last_ingested           TEXT
);

CREATE TABLE IF NOT EXISTS evidence_objects (
    id                      INTEGER PRIMARY KEY,
    uid                     STRING UNIQUE,
    type                    TEXT, -- could be turned into a fk with a set of options
    statement               TEXT, 
    normalized_value        TEXT,
    confidence              TEXT -- could also be turned into a fk with a set of options
);

CREATE TABLE IF NOT EXISTS claims (
    id                      INTEGER PRIMARY KEY,
    uid                     STRING UNIQUE,
    statement               TEXT,
    support_status          TEXT CHECK (support_status IN ({allowed_claim_status})) DEFAULT '{CLAIM_STATUS_ENUM[0]}',
    review_status           TEXT CHECK (review_status in ({allowed_claim_review_status})) DEFAULT '{CLAIM_REVIEW_STATUS_ENUM[1]}',
    risk_note               TEXT
);

CREATE TABLE IF NOT EXISTS requirements (
    id                      INTEGER PRIMARY KEY,
    uid                     STRING UNIQUE,
    jurisdiction            TEXT,
    domain                  TEXT, -- could be fk enum
    requirement_text        TEXT
    -- potential_gaps       TEXT  -- TODO, all gaps are manually created so tracking potential gaps doesn't help anything. 
);

CREATE TABLE IF NOT EXISTS gaps (
    id                      INTEGER PRIMARY KEY,
    uid                     STRING UNIQUE,
    requirement_id          INTEGER,
    rationale               TEXT,
    severity                TEXT CHECK (severity in ({allowed_gaps})),
    recommended_action      TEXT,
    FOREIGN KEY (requirement_id)
        REFERENCES requirements(id)
);
"""

RELATIONSHIPS_SCHEMA = """
-- Many to many 
CREATE TABLE IF NOT EXISTS study_queries (
    nct_id               INTEGER,
    query_uid               TEXT,
    PRIMARY KEY (nct_id, query_uid),
    FOREIGN KEY (nct_id)
        REFERENCES studies(nct_id),
    FOREIGN KEY (query_uid)
        REFERENCES queries(uid)
);

-- Many-to-many sources to evidence  -- this might be unecessary, could be one-to-many (source-to-EOs)
CREATE TABLE IF NOT EXISTS evidence_object_sources (
    source_id               INTEGER,
    evidence_object_id      INTEGER,
    PRIMARY KEY (source_id, evidence_object_id),
    FOREIGN KEY (source_id)
        REFERENCES sources(id),
    FOREIGN KEY (evidence_object_id)
        REFERENCES evidence_objects(id)
);

-- Many-to-many evidence to claims
CREATE TABLE IF NOT EXISTS claim_evidence_objects (
    claim_id                INTEGER,
    evidence_object_id      INTEGER,
    PRIMARY KEY (claim_id, evidence_object_id),
    FOREIGN KEY (claim_id)
        REFERENCES claims(id),
    FOREIGN KEY (evidence_object_id)
        REFERENCES evidence_objects(id)
);

-- Many-to-many-to-many claims to gaps
CREATE TABLE IF NOT EXISTS gap_claims (
    claim_id                INTEGER,
    gap_id                  INTEGER,
    PRIMARY KEY (claim_id, gap_id),
    FOREIGN KEY (claim_id)
        REFERENCES claims(id),
    FOREIGN KEY (gap_id)
        REFERENCES gaps(id)
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # row_factory enables dict-like row access. PostgreSQL equivalent: psycopg2.extras.RealDictCursor
    conn.row_factory = sqlite3.Row

    # DIALECT NOTE: PRAGMA is SQLite-specific. Remove for PostgreSQL.
    conn.cursor().execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")

    # print("conn isolation level:",(conn.isolation_level is None))
    return conn


def init_db() -> None:
    with connect() as conn:
        cursor = conn.cursor()
        cursor.executescript(TABLES_SCHEMA)
        cursor.executescript(RELATIONSHIPS_SCHEMA)
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

def upsert_studies(studies: list[dict], query: dict) -> int:
    with connect() as conn:
        crsr = conn.cursor()
        crsr.execute(
            """
            INSERT INTO queries (uid, text)
            VALUES (:uid, :text)
            ON CONFLICT(uid) 
            DO UPDATE SET text = excluded.text; -- add datetime of text update
            """,

        )
        for study in studies:
            upsert_study(conn, study)
            crsr.execute(
                """
                INSERT INTO study_queries (
                    nct_id, query_uid
                ) VALUES (?, ?)
                ON CONFLICT(nct_id, query_uid) DO NOTHING;
                """,
                (study["nct_id"], query["uid"])
            )
    return len(studies)

def insert_sources(sources: list[dict]) -> int:
    with connect() as conn:
        crsr = conn.cursor()
        crsr.execute(
            """
            INSERT INTO queries (uid, text)
            VALUES (:uid, :text)
            ON CONFLICT(uid) 
            DO UPDATE SET text = excluded.text;
            """,

        )
        for source in sources:
            crsr.execute(
                """
                INSERT INTO sources (
                    uid, type, title, url, target_evidence_types
                ) VALUES (
                    :uid, :type, :title, :url, :target_evidence_types
                )
                """,
                source
            )
    return len(sources)

def insert_and_link_EOs(evidence_objs: list[dict]) -> int:
    # TODO: shift pk generation to RDBM, and enable row replacement
    # Each dict: {uid, type, statement, normalized_value, confidence, source_uids: [...]}
    with connect() as conn:
        crsr = conn.cursor()
        for eo in evidence_objs:
            crsr.execute(
                """
                INSERT INTO evidence_objects (
                    uid, type, statement,
                    normalized_value, confidence
                ) VALUES (
                    :uid, :type, :statement,
                    :normalized_value, :confidence
                )
                """,
                eo,
            )
            eo_id = get_id(conn, "evidence_objects", eo["uid"])
            for source_uid in eo.get("source_uids", []):
                source_id = get_id(conn, "sources", source_uid)
                crsr.execute(
                    """
                    INSERT OR IGNORE INTO evidence_object_sources (
                        source_id, evidence_object_id
                    ) VALUES (?, ?)
                    """,
                    (source_id, eo_id),
                )
        # conn.commit()
    return len(evidence_objs)

def insert_claims(conn, claims: list[dict]) -> int:
    # Each dict: {uid, statement, support_status, review_status, risk_note,}
    allowed_cols = ("uid", "statement", "support_status", "review_status", "risk_note")
    crsr = conn.cursor()
    for claim in claims:
        row = {k: claim[k] for k in allowed_cols if k in claim}
        cols = ", ".join(row.keys())
        placeholders = ", ".join(f":{k}" for k in row.keys())
        crsr.execute(
            f"""
            INSERT INTO claims ({cols})
            VALUES ({placeholders})
            """,
            row,
        )
    return len(claims)

def insert_and_link_claims(claims: list[dict]) -> int:
    # Each dict: {uid, statement, status, risk_note, evidence_object_uids: [...]}
    with connect() as conn:
        insert_claims(conn, claims)
        crsr = conn.cursor()
        for claim in claims:
            claim_id = get_id(conn, "claims", claim["uid"])
            for eo_uid in claim.get("evidence_object_uids", []):
                eo_id = get_id(conn, "evidence_objects", eo_uid)
                crsr.execute(
                    """
                    INSERT INTO claim_evidence_objects (
                        claim_id, evidence_object_id
                    ) VALUES (?, ?)
                    """,
                    (claim_id, eo_id),
                )
    return len(claims)

def insert_requirements(conn, requirements: list[dict]) -> int:
    # TODO: shift pk generation to RDBM, and enable row replacement
    # Each dict: {uid, jurisdiction, domain, requirement_text}
    allowed_cols = [col_dict["name"] for col_dict in get_table_columns(conn, "requirements")]
    crsr = conn.cursor()
    for req in requirements:
        row = {k: req[k] for k in allowed_cols if k in req}
        cols = ", ".join(row.keys())
        placeholders = ", ".join(f":{k}" for k in row.keys())
        crsr.execute(
            f"""
            INSERT INTO requirements ({cols})
            VALUES ({placeholders})
            """,
            row,
        )
    return len(requirements)

def insert_and_link_gaps(conn, gaps: list[dict]) -> int:
    # allowed_cols = ('uid', 'type', 'jurisdiction', 'rationale', 'severity', 'recommended_action')
    allowed_cols = [col_dict["name"] for col_dict in get_table_columns(conn, "gaps")]
    crsr = conn.cursor()
    for gap in gaps:
        row = {k: gap[k] for k in allowed_cols if k in gap}

        if "requirement_uid" in gap:
            row["requirement_id"] = get_id(conn, "requirements", gap["requirement_uid"])

        cols = ", ".join(row.keys())
        placeholders = ", ".join(f":{k}" for k in row.keys())
        crsr.execute(
            f"""
            INSERT INTO gaps ({cols})
            VALUES ({placeholders})
            """,
            row,
        )
        
        for claim_uid in gap["claim_uids"]:
            claim_id = get_id(conn, "claims", claim_uid)
            gap_id = get_id(conn, "gaps", gap["uid"])
            crsr.execute(
                """
                INSERT OR IGNORE INTO gap_claims (
                    claim_id, gap_id
                ) VALUES (?, ?)
                """,
                (claim_id, gap_id),
            )
    return len(gaps)

def update_gap(conn, gap) -> None:
    allowed_cols = [col_dict["name"] for col_dict in get_table_columns(conn, "gaps")]
    crsr = conn.cursor()
    row = {k: gap[k] for k in allowed_cols if k in gap}

    if "requirement_uid" in gap:
        row["requirement_id"] = get_id(conn, "requirements", gap["requirement_uid"])

    col_keys = ", ".join(f"{k} = :{k}" for k in row.keys())
    crsr.execute(
        f"""
        UPDATE gaps SET {col_keys} 
        WHERE uid = :uid
        """,
        row,
    )

def query(sql: str, params: tuple = (), conn = connect()) -> list[sqlite3.Row]:
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

def get_id(conn, table_name, uid) -> int:
    # NOTE: security risk, can be improved later
    return query(f"SELECT id FROM {table_name} WHERE uid = ?", params = (uid,), conn = conn)[0][0]

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

