import json
from datetime import datetime, timezone


def clean_study(raw: dict) -> dict | None:
    ps = raw.get("protocolSection", {})

    nct_id = ps.get("identificationModule", {}).get("nctId")
    title = ps.get("identificationModule", {}).get("briefTitle")
    if not nct_id or not title:
        return None

    status_mod = ps.get("statusModule", {})
    design_mod = ps.get("designModule", {})
    sponsor_mod = ps.get("sponsorCollaboratorsModule", {})
    conditions_mod = ps.get("conditionsModule", {})
    arms_mod = ps.get("armsInterventionsModule", {})
    
    locations_mod = ps.get("contactsLocationsModule", {})
    locations = [
        {
            "facility": loc.get("facility"),
            "city": loc.get("city"),
            "state": loc.get("state"),
            "country": loc.get("country"),
            "lat": loc.get("geoPoint", {}).get("lat"),
            "lon": loc.get("geoPoint", {}).get("lon"),
        }
        for loc in locations_mod.get("locations", [])
    ]
    #designModule
    enrollment_info = design_mod.get("enrollmentInfo", {})
    design_info = design_mod.get("designInfo", {})
    phases = design_mod.get("phases") or []
    phase = "/".join(p for p in phases) or None

    return {
        "nct_id": nct_id,
        "title": title,
        #statusModule
        "status": status_mod.get("overallStatus"),
        "start_date": (status_mod.get("startDateStruct") or {}).get("date"),
        "completion_date": (status_mod.get("completionDateStruct") or {}).get("date"),
        #sponsorCollaboratorsModule
        "sponsor": sponsor_mod.get("leadSponsor", {}).get("name"),
        "sponsor_class": sponsor_mod.get("leadSponsor", {}).get("class"),
        #conditionsModule
        "conditions": json.dumps(conditions_mod.get("conditions") or []),
        "condition_keywords": json.dumps(conditions_mod.get("keywords") or []),
        #armsInterventionsModule
        "interventions": json.dumps(arms_mod.get("interventions", [])),
        "arm_groups": json.dumps(arms_mod.get("armGroups", [])),
        #designModule
        "phase": phase,
        "study_type": design_mod.get("studyType"),
        "enrollment": enrollment_info.get("count"),
        "enrollment_type": enrollment_info.get("type"),
        "masking": design_info.get("maskingInfo", {}).get("masking"),
        "allocation": design_info.get("allocation"),
        "intervention_model": design_info.get("interventionModel"),
        "primary_purpose": design_info.get("primaryPurpose"),

        "locations": json.dumps(locations),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


def clean_studies(raw_studies: list[dict]) -> tuple[list[dict], int]:
    cleaned, dropped = [], 0
    for raw in raw_studies:
        row = clean_study(raw)
        if row is None:
            dropped += 1
        else:
            cleaned.append(row)
    return cleaned, dropped
