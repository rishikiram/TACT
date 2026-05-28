"""FastAPI backend serving clinical trial data from the local SQLite database."""

import json
from pathlib import Path
from typing import Any, Optional

import yaml
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend_py.db import connect, DB_PATH, get_table_columns
from backend_py.data_dictionary import get_annotations

app = FastAPI(title="TACT DB API", description="Serves clinical trial data from local SQLite")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

QUERIES_PATH = Path(__file__).parent / "queries.yaml"


def _load_presets() -> dict:
    with open(QUERIES_PATH) as f:
        return yaml.safe_load(f)


def _parse_json_col(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return []


def _row_to_trial(row) -> dict:
    """Convert a sqlite3.Row to a Trial dict matching the TypeScript interface."""
    r = dict(row)

    # Parse JSON columns
    conditions = _parse_json_col(r.get("conditions"))
    condition_keywords = _parse_json_col(r.get("condition_keywords"))
    interventions = _parse_json_col(r.get("interventions"))
    arm_groups = _parse_json_col(r.get("arm_groups"))
    primary_outcomes = _parse_json_col(r.get("primary_outcomes"))
    secondary_outcomes = _parse_json_col(r.get("secondary_outcomes"))

    # Locations: stored as {facility, city, state, country, lat, lon}
    # TypeScript expects {facility, city, state, country, geoPoint: {lat, lon}}
    raw_locs = _parse_json_col(r.get("locations"))
    locations = []
    countries: set[str] = set()
    for loc in raw_locs:
        transformed: dict[str, Any] = {
            k: loc.get(k) for k in ("facility", "city", "state", "country") if loc.get(k)
        }
        lat = loc.get("lat")
        lon = loc.get("lon")
        if lat is not None and lon is not None:
            transformed["geoPoint"] = {"lat": lat, "lon": lon}
        locations.append(transformed)
        if loc.get("country"):
            countries.add(loc["country"])

    # Derive phases list from boolean columns
    phases = []
    if r.get("phase1"):
        phases.append("PHASE1")
    if r.get("phase2"):
        phases.append("PHASE2")
    if r.get("phase3"):
        phases.append("PHASE3")
    if r.get("phase4"):
        phases.append("PHASE4")

    return {
        "nctId": r.get("nct_id", ""),
        "briefTitle": r.get("title", ""),
        "overallStatus": r.get("status", ""),
        "startDate": r.get("start_date"),
        "startDateType": r.get("start_date_type"),
        "primaryCompletionDate": r.get("primary_completion_date"),
        "primaryCompletionDateType": r.get("primary_completion_date_type"),
        "completionDate": r.get("completion_date"),
        "completionDateType": r.get("completion_date_type"),
        "lastUpdatePost": r.get("last_update_post"),
        "sponsor": r.get("sponsor"),
        "sponsorClass": r.get("sponsor_class"),
        "conditions": conditions,
        "conditionKeywords": condition_keywords,
        "interventions": interventions,
        "armGroups": arm_groups,
        "phases": phases,
        "phase1": bool(r.get("phase1")),
        "phase2": bool(r.get("phase2")),
        "phase3": bool(r.get("phase3")),
        "phase4": bool(r.get("phase4")),
        "phaseText": r.get("phase_text"),
        "studyType": r.get("study_type"),
        "enrollment": r.get("enrollment"),
        "enrollmentType": r.get("enrollment_type"),
        "masking": r.get("masking"),
        "allocation": r.get("allocation"),
        "interventionModel": r.get("intervention_model"),
        "primaryPurpose": r.get("primary_purpose"),
        "locations": locations,
        "multicountry": len(countries) > 1,
        "primaryOutcomes": primary_outcomes,
        "secondaryOutcomes": secondary_outcomes,
    }


def _build_where(
    preset_params: Optional[dict],
    condition: Optional[str],
    status: Optional[str],
    phases: Optional[str],
) -> tuple[str, list]:
    """Build WHERE clause and params list from filter options."""
    clauses: list[str] = []
    params: list[Any] = []

    # Merge preset params with explicit query params
    cond_val = condition
    status_val = status
    phase_filter: Optional[str] = None

    if preset_params:
        if not cond_val and preset_params.get("query.cond"):
            cond_val = preset_params["query.cond"]
        if not status_val and preset_params.get("filter.overallStatus"):
            status_val = preset_params["filter.overallStatus"]
        if preset_params.get("filter.advanced"):
            phase_filter = preset_params["filter.advanced"]

    if cond_val:
        # Match against the conditions JSON column (stored as text)
        terms = [t.strip() for t in cond_val.split(" OR ") if t.strip()]
        sub = " OR ".join("conditions LIKE ?" for _ in terms)
        clauses.append(f"({sub})")
        params.extend(f"%{t}%" for t in terms)

    if status_val:
        clauses.append("status = ?")
        params.append(status_val)

    # Explicit phase param (comma-separated: "2,3")
    if phases:
        phase_nums = [p.strip() for p in phases.split(",")]
        sub = " OR ".join(f"phase{n} = 1" for n in phase_nums if n.isdigit())
        if sub:
            clauses.append(f"({sub})")

    # Preset phase filter (e.g. "PHASE2" or "PHASE2 OR PHASE3")
    if phase_filter:
        phase_tokens = [t.strip() for t in phase_filter.split(" OR ")]
        sub = " OR ".join(
            f"phase{t[-1]} = 1" for t in phase_tokens if t.startswith("PHASE") and t[-1].isdigit()
        )
        if sub:
            clauses.append(f"({sub})")

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


@app.get("/db/presets")
def get_presets():
    presets = _load_presets()
    return {"presets": list(presets.keys())}


@app.get("/db/trials")
def get_trials(
    preset: Optional[str] = Query(None, description="Preset name from queries.yaml"),
    condition: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    phases: Optional[str] = Query(None, description="Comma-separated phase numbers, e.g. '2,3'"),
):
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Database not found at {DB_PATH}. Run: python ingest.py <preset>",
        )

    preset_params: Optional[dict] = None
    if preset:
        all_presets = _load_presets()
        if preset not in all_presets:
            raise HTTPException(status_code=404, detail=f"Preset '{preset}' not found")
        preset_params = all_presets[preset]

    where, params = _build_where(preset_params, condition, status, phases)
    sql = f"SELECT * FROM studies {where}"

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    trials = [_row_to_trial(row) for row in rows]
    return {"trials": trials, "totalCount": len(trials)}


@app.get("/db/dictionary")
def get_dictionary(table: str = Query("studies")):
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail=f"Database not found at {DB_PATH}")

    with connect() as conn:
        # 1. Schema pass
        cols = get_table_columns(conn, table)

        # 2. Stats pass — null count + unique count for all columns in one query
        agg_parts = []
        for col in cols:
            n = col["name"]
            agg_parts.append(f"SUM(CASE WHEN \"{n}\" IS NULL THEN 1 ELSE 0 END) AS \"{n}__nulls\"")
            agg_parts.append(f"COUNT(DISTINCT \"{n}\") AS \"{n}__unique\"")
        stats_row = conn.execute(
            f"SELECT COUNT(*) AS total, {', '.join(agg_parts)} FROM \"{table}\""
        ).fetchone()
        total_rows = stats_row["total"]

        # 3. Sample values pass — 3 distinct non-null values per column
        samples: dict[str, list[str]] = {}
        json_cols = {c["name"] for c in cols if c["type"].upper() == "TEXT"
                     and c["name"] in ("conditions", "condition_keywords", "interventions",
                                       "arm_groups", "locations", "primary_outcomes", "secondary_outcomes")}
        for col in cols:
            n = col["name"]
            if n in json_cols:
                samples[n] = ["[array]"]
            else:
                rows = conn.execute(
                    f"SELECT DISTINCT \"{n}\" FROM \"{table}\" WHERE \"{n}\" IS NOT NULL LIMIT 3"
                ).fetchall()
                samples[n] = [str(r[0]) for r in rows]

        # 4. Annotations pass
        annotations = get_annotations(conn, table)

    columns = []
    for col in cols:
        n = col["name"]
        null_count = stats_row[f"{n}__nulls"] or 0
        null_pct = round(null_count / total_rows * 100, 1) if total_rows else 0.0
        ann = annotations.get(n, {})
        columns.append({
            "name": n,
            "type": col["type"],
            "nullable": not col["notnull"],
            "nullCount": null_count,
            "nullPct": null_pct,
            "uniqueCount": stats_row[f"{n}__unique"] or 0,
            "sampleValues": samples.get(n, []),
            "source": ann.get("source", ""),
            "derivation": ann.get("derivation", ""),
            "plainDescription": ann.get("plain_description", ""),
        })

    return {"table": table, "totalRows": total_rows, "columns": columns}


@app.get("/db/trial/{nct_id}")
def get_trial(nct_id: str):
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail=f"Database not found at {DB_PATH}")

    with connect() as conn:
        row = conn.execute("SELECT * FROM studies WHERE nct_id = ?", (nct_id,)).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")

    return _row_to_trial(row)
