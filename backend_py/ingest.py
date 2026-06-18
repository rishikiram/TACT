"""
Fetch studies from CT.gov, clean them, and write to SQLite.

Usage:
    python ingest.py <preset>        # run a named preset from queries_ctgov.yaml
    python ingest.py --list          # show available presets

Presets are defined in queries_ctgov.yaml.
"""

import argparse
from pathlib import Path

import yaml
import json

from backend_py.clean import clean_ctgov_studies
import backend_py.ctgov as ctgov
import backend_py.db as db
import backend_py.gaps as Gaps
import backend_py.evidence_objects as eos

QUERIES_FILE = Path(__file__).parent / "queries_ctgov.yaml"
REQUIREMENTS_FILE = Path(__file__).parent.parent / "data" / "requirements.yaml"
CLAIMS_FILE = Path(__file__).parent.parent / "data" / "claims.yaml"
EOS_FILE = Path(__file__).parent.parent / "data" / "evidence_objects.yaml"
SOURCES_FILE = Path(__file__).parent.parent / "data" / "sources.yaml"


def ingest_ctgov_studies(conn, query_uid: str, params: dict) -> None:
    print(f"[ingest] query params: {params}")

    # db.init_db()
    # before = db.count()

    print("[ingest] fetching from CT.gov...")
    raw_studies = ctgov.fetch_all_pages(params)
    print(f"[ingest] fetched {len(raw_studies)} studies")

    cleaned, dropped = clean_ctgov_studies(raw_studies)
    print(f"[ingest] cleaned: {len(cleaned)}, dropped (missing id/title): {dropped}")

    query = {"uid":query_uid, "text":json.dumps(params)}
    db.upsert_studies(conn, cleaned, query)
    # after = db.count()
    # print(f"[ingest] done — db grew from {before} → {after} studies")

def ingest_tracible_stack_test() -> None:
    db.init_db()

    sources_before = db.query("SELECT COUNT(*) FROM sources")[0][0]
    EOs_before = db.query("SELECT COUNT(*) FROM evidence_objects")[0][0]
    claims_before = db.query("SELECT COUNT(*) FROM claims")[0][0]
    requirements_before = db.query("SELECT COUNT(*) FROM requirements")[0][0]
    gaps_before = db.query("SELECT COUNT(*) FROM gaps")[0][0]

    with db.connect() as conn:
        target_evidence_types = ["design", "population", "endpoints", "comparator status"]
        db.insert_sources(conn, [
            {
                "uid": "SRC-002", 
                "type": "simulated internal document", 
                "title": "VER-101 Phase II protocol synopsis",
                "url": "file://First Example NSCLC Case Skeleton_27May2026.pdf",
                "target_evidence_types": json.dumps(target_evidence_types)
            }
        ])

        db.insert_and_link_EOs(conn, [
            {
                "uid": "EO-003",
                "type": "comparator", 
                "statement": "No randomized comparator arm is included", 
                "normalized_value": "No head-to-head comparator",
                "confidence":  "high",
                "source_uids": ["SRC-002"]
            }
        ])
        
        with open(CLAIMS_FILE) as f:
            claims_data = yaml.safe_load(f)
        claims = next(iter(claims_data.values())) # get first value of {key:value} pairs
        claims.sort(key=lambda f: f["uid"])
        db.insert_claims(conn, claims)

        potential_gaps = ["comparator uncertainty"]
        db.insert_requirements(conn, [
            {
                "uid": "REQ-NICE-001",
                "jurisdiction": "NICE/England",
                "domain": "comparator",
                "requirement_text": "Evidence should support relative clinical effectiveness against a relevant comparator.",
                "potential_gaps": json.dumps(potential_gaps)
            }
        ])

        db.insert_and_link_gaps(conn, [
            {
                "uid": "GAP-001",
                "type": "comparator uncertainty",
                "severity": "high",
                "jurisdiction": "NICE/England",
                "rationale": "no randomized comparator",
                "recommended_action": "Assess indirect comparison feasibility and RWE augmentation plan.",
                "claim_uid_requirement_uid_trios": [("CLAIM-002", "REQ-NICE-001")]
            }
        ])

    sources_after = db.query("SELECT COUNT(*) FROM sources")[0][0]
    EOs_after = db.query("SELECT COUNT(*) FROM evidence_objects")[0][0]
    claims_after = db.query("SELECT COUNT(*) FROM claims")[0][0]
    requirements_after = db.query("SELECT COUNT(*) FROM requirements")[0][0]
    gaps_after = db.query("SELECT COUNT(*) FROM gaps")[0][0]

    
    print(
        "----------------\n"
        f"Sources inserted: {sources_after - sources_before}\n"
        f"EOs inserted: {EOs_after - EOs_before}\n"
        f"Claims inserted: {claims_after - claims_before}\n"
        f"Requirements inserted: {requirements_after - requirements_before}\n"
        f"Gaps inserted: {gaps_after - gaps_before}"
    )

def build_traceable_stack() -> None:
    db.init_db()
    tables = ["sources", "evidence_objects", "queries", "studies", "claims", "requirements", "gaps"]
    before = [db.count(t) for t in tables]

    with db.connect() as conn:
        # ingest manual EOs
        with open(SOURCES_FILE) as f:
            sources_data = yaml.safe_load(f)
        sources = next(iter(sources_data.values()))
        sources.sort(key=lambda f: f["uid"])
        db.insert_sources(conn, sources)

        # ingest manual EOs
        with open(EOS_FILE) as f:
            eos_data = yaml.safe_load(f)
        eos = next(iter(eos_data.values()))
        eos.sort(key=lambda f: f["uid"])
        db.insert_and_link_EOs(conn, eos)

        # ingest requirements
        with open(REQUIREMENTS_FILE) as f:
            reqs_data = yaml.safe_load(f)
        requirements = next(iter(reqs_data.values()))
        requirements.sort(key=lambda f: f["uid"])
        db.insert_requirements(conn, requirements)

        # build potential gaps, and claims that determine the gaps
        with open(CLAIMS_FILE) as f:
            claims_data = yaml.safe_load(f)
        claims = next(iter(claims_data.values())) 
        claims.sort(key=lambda f: f["uid"])
        db.insert_and_link_claims(conn, claims)

        gap_objs = build_gap_objects()
        gaps = []
        for g in gap_objs:
            g.set_severity_and_rationale(conn)
            gaps.append(g.to_dict())
        db.insert_and_link_gaps(conn, gaps)
        
    # ingest sources
        queries_to_use = ["nsclc_kras", "nsclc_2line"]
        print("Only using queries: ", queries_to_use)
        with open(QUERIES_FILE) as f:
            queries = yaml.safe_load(f)
        for uid,params in queries.items():
            if uid in queries_to_use:
                ingest_ctgov_studies(conn, uid, params)

    # generate set of evidence objects from historical data
        sources, comparator_eos = build_comparator_EOs(conn, "nsclc_2line") # NOTE: hardcoded
        print(len(sources), len(comparator_eos))
        db.insert_sources(conn, sources)
        eo_ids = db.insert_and_link_EOs(conn, comparator_eos)

    # connect evidence objects to support or disprove claims
        db.link_EOs_to_claims_of_type(conn, eo_ids, "comparator")

    # update gap severity - ✅
        # update_claim_status(conn, "CLAIM-006", "supported") # works
    # build (traceable) report 

    after = [db.count(t) for t in tables]
    s = "----------------\n"
    for i,t in enumerate(tables):
        s += f"{t} inserted: {after[i] - before[i]}\n"
    print(s)

def build_gap_objects() -> list[Gaps.Gap]:
    gap_list = []
    gap_list.append(Gaps.Gap_001())
    gap_list.append(Gaps.Gap_002())
    gap_list.append(Gaps.Gap_003())
    gap_list.append(Gaps.Gap_004())
    gap_list.append(Gaps.Gap_005())
    gap_list.append(Gaps.Gap_006())
    return gap_list

def build_comparator_EOs(conn, query_uid) -> tuple:
    """
        Args:
            conn: connection to database 
            query_uid: uid of the query that is associsated with a set of CTGov studies. 
                These are the studies used when extracting trial arms for potential comparators
    """

    # POTENTIAL_CONTROL_GROUPS_QUERY_UID = "nsclc_2line"
    control_group_nctids = eos.get_nctids(conn, query_uid)
    all_group_types = set(eos.GROUP_TYPES)
    evidence_list = eos.get_potential_comparator_groups_of_type(control_group_nctids, list(all_group_types)) 

    # build 'source' related to this aact query
    sources = [
        {
            "url": "aact-db.ctti-clinicaltrials.org",
            "title": "Potential Comparator Groups with Results",
            "type": "AACT-CTTI query",
            "uid": "SRC-101",
            "how_to_recreate": "query tables design_groups and result_groups. Link by nct_id and title. This link is not enfored for all ctgov studies, but some studies follow it. Pull fields {nct_id, title, dg,id, rg,id, dg.group_type, rg.description}"
        }
    ]
    potential_control_groups = [{
            # "uid": , TODO how can I derrive a stable human name...
            "nct_id": evi["nct_id"],
            "source_uids": ["SRC-101"],
            "normalized_value": evi["group_type"],
            "type": "comparator", # TODO use a standard enumerator somehow
            "statement": json.dumps(evi, indent=2),
            "confidence": "low" 
        }
        for evi in evidence_list]
    return (sources, potential_control_groups)


def update_claim_status(conn, claim_uid, support_status) -> None:
    cursor = conn.cursor()
    cursor.execute("UPDATE claims SET support_status = ? WHERE uid = ?", (support_status, claim_uid))
    q = """
    SELECT gaps.uid
    FROM gaps
    JOIN gap_claims ON gaps.id = gap_claims.gap_id
    JOIN claims ON claims.id = gap_claims.claim_id
    WHERE claims.uid = ?
    """
    cursor.execute(q, (claim_uid,))
    gap_uids = list(cursor.fetchall()[0])

    # update gaps by running gap severity function
    for gap_uid in gap_uids:
        gap_obj = Gaps.GAP_REGISTRY[gap_uid]() # type: ignore
        gap_obj.set_severity_and_rationale(conn)
        db.update_gap(conn, gap_obj.to_dict())

    
# ----------------

def build_traceable_stack_v2() -> None:
    db.init_db()
    tables = ["sources", "evidence_objects", "queries", "studies", "claims", "requirements", "gaps"]
    before = [db.count(t) for t in tables]

    with db.connect() as conn:
        
    # ingest sources
        queries_to_use = ["nsclc_ppp"]
        print("Using queries: ", queries_to_use)
        with open(QUERIES_FILE) as f:
            queries = yaml.safe_load(f)
        for uid,params in queries.items():
            if uid in queries_to_use:
                ingest_ctgov_studies(conn, uid, params)
        # filter for studies with results

    # generate set of evidence objects from historical data
        sources, comparator_eos = build_comparator_EOs(conn, "nsclc_ppp")
        print(len(sources), len(comparator_eos))
        db.insert_sources(conn, sources)
        eo_ids = db.insert_and_link_EOs(conn, comparator_eos)

    # connect evidence objects to support or disprove claims
        # TODO, do I want this?
        # db.link_EOs_to_claims_of_type(conn, eo_ids, "comparator")

    # build (traceable) report 

    after = [db.count(t) for t in tables]
    s = "----------------\n"
    for i,t in enumerate(tables):
        if not (after[i] == before[i]):
            s += f"{t} inserted: {after[i] - before[i]}\n"
    print(s)

def testing():
    print( db.query("SELECT COUNT(*) FROM sources")[0][0])

if __name__ == "__main__":
    build_traceable_stack_v2()