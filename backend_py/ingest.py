#!/usr/bin/env python3
"""
Fetch studies from CT.gov, clean them, and write to SQLite.

Usage:
    python ingest.py --condition "cancer" --status "RECRUITING"
    python ingest.py --condition "diabetes" --sponsor "NIH"

Any key=value pair maps directly to CT.gov API query params.
See https://clinicaltrials.gov/data-api/api for the full param reference.
"""

import argparse
import sys

from clean import clean_studies
from ctgov import fetch_all_pages
from db import init_db, upsert_studies, count


CT_GOV_PARAM_ALIASES = {
    "condition": "query.cond",
    "sponsor":   "query.spons",
    "status":    "filter.overallStatus",
    "phase":     "filter.phase",
    "type":      "filter.studyType",
}


def parse_args() -> dict:
    parser = argparse.ArgumentParser(description="Ingest CT.gov studies into SQLite.")
    parser.add_argument("--condition", help="Condition or disease (query.cond)")
    parser.add_argument("--sponsor",   help="Sponsor name (query.spons)")
    parser.add_argument("--status",    help="Overall status filter (e.g. RECRUITING)")
    parser.add_argument("--phase",     help="Phase filter (e.g. PHASE2)")
    parser.add_argument("--type",      help="Study type filter (e.g. INTERVENTIONAL)")
    args = parser.parse_args()

    params = {}
    for arg_name, ct_param in CT_GOV_PARAM_ALIASES.items():
        value = getattr(args, arg_name)
        if value:
            params[ct_param] = value

    if not params:
        parser.error("Provide at least one filter (--condition, --sponsor, --status, --phase, --type)")

    return params


def ingest(params: dict) -> None:
    print(f"[ingest] query params: {params}")

    init_db()
    before = count()

    print("[ingest] fetching from CT.gov...")
    raw_studies = fetch_all_pages(params)
    print(f"[ingest] fetched {len(raw_studies)} studies")

    cleaned, dropped = clean_studies(raw_studies)
    print(f"[ingest] cleaned: {len(cleaned)}, dropped (missing id/title): {dropped}")

    upsert_studies(cleaned)
    after = count()
    print(f"[ingest] done — db grew from {before} → {after} studies")


if __name__ == "__main__":
    params = parse_args()
    ingest(params)
