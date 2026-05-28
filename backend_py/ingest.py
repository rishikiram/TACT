#!/usr/bin/env python3
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

from clean import clean_ctgov_studies
from ctgov import fetch_all_pages
from db import init_db, upsert_studies, count

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


def ingest(params: dict) -> None:
    print(f"[ingest] query params: {params}")

    init_db()
    before = count()

    print("[ingest] fetching from CT.gov...")
    raw_studies = fetch_all_pages(params)
    print(f"[ingest] fetched {len(raw_studies)} studies")

    cleaned, dropped = clean_ctgov_studies(raw_studies)
    print(f"[ingest] cleaned: {len(cleaned)}, dropped (missing id/title): {dropped}")

    upsert_studies(cleaned)
    after = count()
    print(f"[ingest] done — db grew from {before} → {after} studies")


if __name__ == "__main__":
    presets = load_presets()
    params = parse_args(presets)
    ingest(params)
