import backend_py.aact_ctti as aact
import backend_py.db as db

def get_nctids(query_uid: str) -> list[str]:
    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT studies.nct_id
                FROM studies
                JOIN study_queries ON studies.nct_id = study_queries.nct_id
                WHERE study_queries.query_uid = ?
            """,
            (query_uid,)
        )
        r = [row[0] for row in cursor.fetchall()]
    return r

def get_SOC_compartor_studies(query_uid: str) -> list[dict]:
    nct_ids = get_nctids(query_uid)
    if not nct_ids:
        return []
    with aact.connect_aact() as conn:
        cur = conn.cursor()
        # I dont want to use dssign groups, as they are not necesarilty related to the outocme grpups
        cur.execute(
            """
            SELECT
                rg.nct_id,
                rg.group_type,
                rg.title        AS arm_title,
                rg.description  AS arm_description,
                o.title         AS outcome_title,
                o.outcome_type,
                om.param_type,
                om.param_value,
                om.dispersion_type,
                om.dispersion_value,
                om.units
            FROM result_groups rg
            JOIN outcome_measurements om
                ON  om.nct_id          = rg.nct_id
                AND om.ctgov_group_code = rg.ctgov_group_code
            JOIN outcomes o
                ON  o.id = om.outcome_id
            WHERE rg.nct_id = ANY(%s)
              AND rg.result_type = 'Outcome'
              AND rg.group_type IN (
                    'Active Comparator',
                    'Placebo Comparator',
                    'Sham Comparator',
                    'No Intervention'
              )
            ORDER BY rg.nct_id, rg.title, o.title
            """,
            (nct_ids,)
        )
        rows = cur.fetchall()
    return [
        {
            "nct_id":            row[0],
            "group_type":        row[1],
            "arm_title":         row[2],
            "arm_description":   row[3],
            "outcome_title":     row[4],
            "outcome_type":      row[5],
            "param_type":        row[6],
            "param_value":       row[7],
            "dispersion_type":   row[8],
            "dispersion_value":  row[9],
            "units":             row[10],
        }
        for row in rows
    ]

def get_comparator_outcome_measurments(study_nctids: list[str]) -> list[dict]:
    with aact.connect_aact() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                om.nct_id,
                om.ctgov_group_code,
                o.title,
                o.outcome_type,
                om.param_type,
                om.param_value,
                om.dispersion_type,
                om.dispersion_value,
                om.units
            FROM outcome_measurements om
            JOIN outcomes o ON o.id = om.outcome_id
            WHERE om.nct_id = ANY(%s)
            ORDER BY om.nct_id, o.title
            """,
            (study_nctids,)
        )
        rows = cur.fetchall()
    return [
        {
            "nct_id":           row[0],
            "ctgov_group_code": row[1],
            "outcome_title":    row[2],
            "outcome_type":     row[3],
            "param_type":       row[4],
            "param_value":      row[5],
            "dispersion_type":  row[6],
            "dispersion_value": row[7],
            "units":            row[8],
        }
        for row in rows
    ]

def get_potential_comparator_groups(study_nctids: list[str]) -> list[dict]:
    with aact.connect_aact() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT t.nct_id, t.group_type, t.title, t.description FROM design_groups as t 
            WHERE t.nct_id = ANY(%s)
            """,
            (study_nctids,)
        ) 
        rows = cur.fetchall()
    r = [{"nct_id": row[0], "group_type": row[1], "title": row[2], "description": row[3]} for row in rows]
    return r

def get_potential_comparator_endpoints(study_nctids: list[str]) -> list[dict]:
    with aact.connect_aact() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT t.nct_id, t.outcome_type, t.measure, t.timeframe, t.population, t.description FROM design_outcomes AS t 
            WHERE t.nct_id = ANY(%s)
            """,
            (study_nctids,)
        )
        rows = cur.fetchall()
    r = [{"nct_id": row[0], "outcome_type": row[1], "measure": row[2], "timeframe": row[3], "population": row[4], "description": row[5]} for row in rows]
    return r

def get_something(study_nctids: list[str]) -> list[dict]:
    with aact.connect_aact() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT t.nct_id, t.outcome_type, t.measure, t.timeframe, t.population, t.description FROM design_outcomes AS t 
            WHERE t.nct_id = ANY(%s)
            """,
            (study_nctids,)
        )
        rows = cur.fetchall()
    r = [{"nct_id": row[0], "outcome_type": row[1], "measure": row[2], "timeframe": row[3], "population": row[4], "description": row[5]} for row in rows]
    return r

def get_stuff(study_nctids: list[str]) -> list[dict]:
    with aact.connect_aact() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT t.nct_id, t.outcome_type, t.measure, t.timeframe, t.population, t.description FROM design_outcomes AS t 
            WHERE t.nct_id = ANY(%s)
            """,
            (study_nctids,)
        )
        rows = cur.fetchall()
    r = [{"nct_id": row[0], "outcome_type": row[1], "measure": row[2], "timeframe": row[3], "population": row[4], "description": row[5]} for row in rows]
    return r

def get_foo(study_nctids: list[str]) -> list[dict]:
    with aact.connect_aact() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT t.nct_id, t.outcome_type, t.measure, t.timeframe, t.population, t.description FROM design_outcomes AS t 
            WHERE t.nct_id = ANY(%s)
            """,
            (study_nctids,)
        )
        rows = cur.fetchall()
    r = [{"nct_id": row[0], "outcome_type": row[1], "measure": row[2], "timeframe": row[3], "population": row[4], "description": row[5]} for row in rows]
    return r

# given ids, pull data from db.studies table or aact db.

# n reported events
    # reported_events event_count for all events
    # 
# table designs
#   masking 
#       subject_masked
#       caregiver_masked
#       investigator_masked
#       outcomes_assessor_masked

# table eligibilities
#   sampling_method

# NOTE: only one study related to KRAS G12C inhibitores has results in ctgov. 
#   6 others have publications, ["41037823", "40523897", "36399068", "41940628","41325755","40333694"]


"""
SELECT o.* FROM outcome_measurements as o 
WHERE o.nct_id IN 
('NCT07416058', 'NCT05769764', 'NCT05002270', 'NCT05786924', 'NCT05578092', 'NCT06119581', 'NCT05480865', 'NCT06026410', 'NCT06793215', 'NCT05485974', 'NCT05853575', 'NCT06447662', 'NCT04975256', 'NCT04699188', 'NCT05375994', 'NCT07601048', 'NCT06497556', 'NCT06300177', 'NCT07288034', 'NCT04330664', 'NCT05492045', 'NCT05840510', 'NCT06481813', 'NCT04585035', 'NCT07543172', 'NCT05074810', 'NCT04967079', 'NCT05585320', 'NCT06130254', 'NCT05374538', 'NCT05358249', 'NCT05288205') 
"""

"""
SELECT COUNT(*) FROM reported_events as t 
WHERE event_type = 'serious' AND event_count > 0 AND
t.nct_id IN ('NCT07416058', 'NCT05769764', 'NCT05002270', 'NCT05786924', 'NCT05578092', 'NCT06119581', 'NCT05480865', 'NCT06026410', 'NCT06793215', 'NCT05485974', 'NCT05853575', 'NCT06447662', 'NCT04975256', 'NCT04699188', 'NCT05375994', 'NCT07601048', 'NCT06497556', 'NCT06300177', 'NCT07288034', 'NCT04330664', 'NCT05492045', 'NCT05840510', 'NCT06481813', 'NCT04585035', 'NCT07543172', 'NCT05074810', 'NCT04967079', 'NCT05585320', 'NCT06130254', 'NCT05374538', 'NCT05358249', 'NCT05288205') 
"""

"""
SELECT t.* FROM reported_event_totals as t 
WHERE t.nct_id IN ('NCT07416058', 'NCT05769764', 'NCT05002270', 'NCT05786924', 'NCT05578092', 'NCT06119581', 'NCT05480865', 'NCT06026410', 'NCT06793215', 'NCT05485974', 'NCT05853575', 'NCT06447662', 'NCT04975256', 'NCT04699188', 'NCT05375994', 'NCT07601048', 'NCT06497556', 'NCT06300177', 'NCT07288034', 'NCT04330664', 'NCT05492045', 'NCT05840510', 'NCT06481813', 'NCT04585035', 'NCT07543172', 'NCT05074810', 'NCT04967079', 'NCT05585320', 'NCT06130254', 'NCT05374538', 'NCT05358249', 'NCT05288205') 
"""

# potential comparators
"""
SELECT t.* FROM design_groups as t 
WHERE t.nct_id IN ('NCT07416058', 'NCT05769764', 'NCT05002270', 'NCT05786924', 'NCT05578092', 'NCT06119581', 'NCT05480865', 'NCT06026410', 'NCT06793215', 'NCT05485974', 'NCT05853575', 'NCT06447662', 'NCT04975256', 'NCT04699188', 'NCT05375994', 'NCT07601048', 'NCT06497556', 'NCT06300177', 'NCT07288034', 'NCT04330664', 'NCT05492045', 'NCT05840510', 'NCT06481813', 'NCT04585035', 'NCT07543172', 'NCT05074810', 'NCT04967079', 'NCT05585320', 'NCT06130254', 'NCT05374538', 'NCT05358249', 'NCT05288205') 
"""

# n withdrawals
"""
SELECT t.* FROM drop_withdrawals as t 
WHERE t.nct_id IN ('NCT07416058', 'NCT05769764', 'NCT05002270', 'NCT05786924', 'NCT05578092', 'NCT06119581', 'NCT05480865', 'NCT06026410', 'NCT06793215', 'NCT05485974', 'NCT05853575', 'NCT06447662', 'NCT04975256', 'NCT04699188', 'NCT05375994', 'NCT07601048', 'NCT06497556', 'NCT06300177', 'NCT07288034', 'NCT04330664', 'NCT05492045', 'NCT05840510', 'NCT06481813', 'NCT04585035', 'NCT07543172', 'NCT05074810', 'NCT04967079', 'NCT05585320', 'NCT06130254', 'NCT05374538', 'NCT05358249', 'NCT05288205')
"""

# eligibility criteria
"""
SELECT t.criteria FROM eligibilities as t 
WHERE t.nct_id IN ('NCT07416058', 'NCT05769764', 'NCT05002270', 'NCT05786924', 'NCT05578092', 'NCT06119581', 'NCT05480865', 'NCT06026410', 'NCT06793215', 'NCT05485974', 'NCT05853575', 'NCT06447662', 'NCT04975256', 'NCT04699188', 'NCT05375994', 'NCT07601048', 'NCT06497556', 'NCT06300177', 'NCT07288034', 'NCT04330664', 'NCT05492045', 'NCT05840510', 'NCT06481813', 'NCT04585035', 'NCT07543172', 'NCT05074810', 'NCT04967079', 'NCT05585320', 'NCT06130254', 'NCT05374538', 'NCT05358249', 'NCT05288205')
"""

# published results
"""
SELECT t.* FROM study_references as t 
WHERE t.nct_id IN ('NCT07416058', 'NCT05769764', 'NCT05002270', 'NCT05786924', 'NCT05578092', 'NCT06119581', 'NCT05480865', 'NCT06026410', 'NCT06793215', 'NCT05485974', 'NCT05853575', 'NCT06447662', 'NCT04975256', 'NCT04699188', 'NCT05375994', 'NCT07601048', 'NCT06497556', 'NCT06300177', 'NCT07288034', 'NCT04330664', 'NCT05492045', 'NCT05840510', 'NCT06481813', 'NCT04585035', 'NCT07543172', 'NCT05074810', 'NCT04967079', 'NCT05585320', 'NCT06130254', 'NCT05374538', 'NCT05358249', 'NCT05288205')
"""
