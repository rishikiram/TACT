"""
Fetch studies from CT.gov, clean them, and write to SQLite.

Usage:
    python ingest.py <preset>        # run a named preset from queries.yaml
    python ingest.py --list          # show available presets

Presets are defined in queries.yaml.
"""

import argparse
from pathlib import Path

import yaml
import json

from backend_py.clean import clean_ctgov_studies
from backend_py.ctgov import fetch_all_pages
# from backend_py.db import init_db, upsert_studies, count, query
import backend_py.db as db

QUERIES_FILE = Path(__file__).parent / "queries.yaml"


def load_presets() -> dict:
    with open(QUERIES_FILE) as f:
        return yaml.safe_load(f)


def parse_args(presets: dict):
    parser = argparse.ArgumentParser(description="Ingest CT.gov studies into SQLite.")
    parser.add_argument("preset", nargs="?", help="Preset name from queries.yaml")
    parser.add_argument("--list", action="store_true", help="List available presets")
    args = parser.parse_args()

    if args.list:
        print("Available presets:")
        for name, params in presets.items():
            print(f"  {name}")
            # for k, v in params.items():
            #     print(f"    {k}: {v}")
        raise SystemExit(0)

    if not args.preset:
        parser.error("Provide a preset name, or --list to see options")

    if args.preset not in presets:
        parser.error(f"Unknown preset '{args.preset}'. Run --list to see options.")

    return presets[args.preset]


def ingest_studies(params: dict) -> None:
    print(f"[ingest] query params: {params}")

    db.init_db()
    before = db.count()

    print("[ingest] fetching from CT.gov...")
    raw_studies = fetch_all_pages(params)
    print(f"[ingest] fetched {len(raw_studies)} studies")

    cleaned, dropped = clean_ctgov_studies(raw_studies)
    print(f"[ingest] cleaned: {len(cleaned)}, dropped (missing id/title): {dropped}")

    db.upsert_studies(cleaned)
    after = db.count()
    print(f"[ingest] done — db grew from {before} → {after} studies")


def ingest_tracible_stack() -> None:
    db.init_db()

    sources_before = db.query("SELECT COUNT(*) FROM sources")[0][0]
    EOs_before = db.query("SELECT COUNT(*) FROM evidence_objects")[0][0]
    claims_before = db.query("SELECT COUNT(*) FROM claims")[0][0]
    requirements_before = db.query("SELECT COUNT(*) FROM requirements")[0][0]
    gaps_before = db.query("SELECT COUNT(*) FROM gaps")[0][0]

    target_evidence_types = ["design", "population", "endpoints", "comparator status"]
    db.insert_sources([
        {
            "source_id": 2, 
            "type": "simulated internal document", 
            "title": "VER-101 Phase II protocol synopsis",
            "url": "file://First Example NSCLC Case Skeleton_27May2026.pdf",
            "target_evidence_types": json.dumps(target_evidence_types)
        }
    ])

    db.insert_and_link_EOs([
        {
            "evidence_object_id": 3,
            "type": "comparator", 
            "statement": "No randomized comparator arm is included", 
            "normalized_value": "No head-to-head comparator",
            "confidence":  "high",
            "source_ids": [2]
        }
    ])

    db.insert_and_link_claims([
        {
            "claim_id": 2,
            "statement": "VER-101 improves progression-free survival versus current standard of care.",
            "status": "unsupported",
            "risk_note": "No randomized comparator and no comparative PFS estimate.",
            "evidence_object_ids": [3] #,5]
        }
    ])

    potential_gaps = ["comparator uncertainty"]
    db.insert_requirements([
        {
            "requirement_id": 1,
            "jurisdiction": "NICE/England",
            "domain": "comparator",
            "expectation": "Evidence should support relative clinical effectiveness against a relevant comparator.",
            "potential_gaps": json.dumps(potential_gaps)
        }
    ])

    db.insert_and_link_gaps([
        {
            "gap_id": 1,
            "type": "comparator uncertainty",
            "severity": "high",
            "jurisdiction": "NICE/England",
            "rationale": "no randomized comparator",
            "recommended_action": "Assess indirect comparison feasibility and RWE augmentation plan.",
            "claim_id_requirement_id_trios": [(2, 1)]
        }
    ])

    sources_after = db.query("SELECT COUNT(*) FROM sources")[0][0]
    EOs_after = db.query("SELECT COUNT(*) FROM evidence_objects")[0][0]
    claims_after = db.query("SELECT COUNT(*) FROM claims")[0][0]
    requirements_after = db.query("SELECT COUNT(*) FROM requirements")[0][0]
    gaps_after = db.query("SELECT COUNT(*) FROM gaps")[0][0]

    
    print(
        f"Sources inserted: {sources_after - sources_before}\n"
        f"EOs inserted: {EOs_after - EOs_before}\n"
        f"Claims inserted: {claims_after - claims_before}\n"
        f"Requirements inserted: {requirements_after - requirements_before}\n"
        f"Gaps inserted: {gaps_after - gaps_before}"
    )


if __name__ == "__main__":
    presets = load_presets()
    params = parse_args(presets)
    # ingest_studies(params)
    ingest_tracible_stack()

def testing():
    print( db.query("SELECT COUNT(*) FROM sources")[0][0])
