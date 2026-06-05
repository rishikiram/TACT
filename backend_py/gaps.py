from dataclasses import dataclass, field, asdict
import backend_py.db as db

GAP_SEVERITY_ENUM = db.GAP_SEVERITY_ENUM
CLAIM_STATUS_ENUM = db.CLAIM_STATUS_ENUM
assert (GAP_SEVERITY_ENUM == ("no data", "non-conclusive", "high", "medium", "low", "zero"))

SUPPORTED = CLAIM_STATUS_ENUM[-1]
assert (CLAIM_STATUS_ENUM[-1] == "supported")



@dataclass
class Gap:
    # User Input
    uid: str 
    requirement_uid: str 
    # Set by Class Functions
    rationale: str = "NOT SET, something is wrong"
    recommended_action: str = "NOT SET, something is wrong"
    # defaults
    review_status: str = "unreviewed"
    severity: str = GAP_SEVERITY_ENUM[0] # == unknown (default?)
    claim_uids: list[str] = field(default_factory=list) # no links

    def severity_score(self, conn) -> tuple:
        raise NotImplementedError
    def set_severity_and_rationale(self, conn) -> None:
         self.severity, self.rationale = self.severity_score(conn)

    def get_claim_status(self, conn, claim_uid) -> str:
        return db.query("SELECT support_status FROM claims WHERE uid = ?", params=(claim_uid,), conn=conn)[0][0]
    def get_claim_statement(self, conn, claim_uid) -> str:
        return db.query("SELECT statement FROM claims WHERE uid = ?", params=(claim_uid,), conn=conn)[0][0]
    
    def to_dict(self) -> dict:
        return asdict(self)
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(uid={self.uid}, severity={self.severity})"


@dataclass
class Gap_001(Gap):
    uid: str = "GAP-001"
    requirement_uid: str = "REQ-NICE-COMP-001"

    # rationale: str = "no randomized comparator"
    # recommended_action: str = "Assess indirect comparison feasibility and RWE augmentation plan"

    SOC_comparator_claim: str = "CLAIM-006"
    direct_comparator_claim: str = "CLAIM-007"
    placebo_comparator_claim: str = "CLAIM-008"
    indirect_comparator_claim: str = "CLAIM-009"

    def __post_init__(self):
        self.claim_uids = [self.SOC_comparator_claim, self.direct_comparator_claim, self.placebo_comparator_claim, self.indirect_comparator_claim]

    def severity_score(self, conn) -> tuple:
        score = 1 # GAP_SEVERITY_ENUM[4] == supported
        new_rationale = []
        
        # If standard-of-care comparator is present
        if self.get_claim_status(conn, self.SOC_comparator_claim) == SUPPORTED:
            score += 2
            new_rationale += ["Standard of Care comparator is present"]

        if self.get_claim_status(conn, self.placebo_comparator_claim) == SUPPORTED:
            score += 1
            new_rationale += ["Placebo comparator is present"]

        if self.get_claim_status(conn, self.direct_comparator_claim) == SUPPORTED:
            score += 1
            new_rationale += ["Direct comparator is present"]

        if self.get_claim_status(conn, self.indirect_comparator_claim) == SUPPORTED:
            score += 1
            new_rationale += ["Indirect comparator is present"]

        score = min(5, score)
        if len(new_rationale) == 0:
                new_rationale = ["no randomized comparator"]

        return (GAP_SEVERITY_ENUM[score], "; ".join(new_rationale)+".")

@dataclass
class Gap_002(Gap):
    uid: str = "GAP-002"
    requirement_uid: str = "REQ-US-ENDPT-001"

    # rationale: str = "EO-006: OS immature; EO-004: ORR primary"
    # recommended_action: str = "Track longer follow-up; define durability evidence plan."
    
    orr_claim: str = "CLAIM-001"
    pfs_claim: str = "CLAIM-002"
    os_claim: str = "CLAIM-010"

    def __post_init__(self):
        self.claim_uids = [self.orr_claim, self.pfs_claim, self.os_claim]

    def severity_score(self, conn) -> tuple:
        score = 1 # GAP_SEVERITY_ENUM[4] == supported
        new_rationale = []
        if self.get_claim_status(conn, self.os_claim) == SUPPORTED:
            score += 3
            new_rationale += ["Overall Survival is shown"]

        if self.get_claim_status(conn, self.pfs_claim) == SUPPORTED:
            score += 2
            new_rationale += ["Significant progression free survival is shown"]

        if self.get_claim_status(conn, self.orr_claim) == SUPPORTED:
            score += 1
            new_rationale += ["A meaningful tumor response is shown"]

        score = min(5, score)
        if len(new_rationale) == 0:
                new_rationale += ["no randomized comparator"]

        return (GAP_SEVERITY_ENUM[score], "; ".join(new_rationale))
    
@dataclass
class Gap_003(Gap):
    uid: str = "GAP-003"
    requirement_uid: str = "REQ-NICE-QOL-001"
    
    QoL_claim: str = "CLAIM-003"
    PRO_claim: str = "CLAIM-011"
    safety_and_convenience_claim: str = "CLAIM-004"

    def __post_init__(self):
        self.claim_uids = [self.QoL_claim, self.PRO_claim, self.safety_and_convenience_claim]

    def severity_score(self, conn) -> tuple:
        score = 1 # GAP_SEVERITY_ENUM[4] == supported
        new_rationale = []
        if self.get_claim_status(conn, self.QoL_claim) == SUPPORTED:
            score += 2
            new_rationale += [self.get_claim_statement(conn, self.QoL_claim)] # this can be done by the relational database w/ reusing the text

        if  self.get_claim_status(conn, self.PRO_claim) == SUPPORTED:
            score += 2
            new_rationale += [self.get_claim_statement(conn, self.PRO_claim)]

        if self.get_claim_status(conn, self.safety_and_convenience_claim) == SUPPORTED:
            score += 1
            new_rationale += [self.get_claim_statement(conn, self.safety_and_convenience_claim)]

        score = min(5, score)
        if len(new_rationale) == 0:
                new_rationale += ["No QoL changes or PROs supporting VER-101"]

        return (GAP_SEVERITY_ENUM[score], "; ".join(new_rationale))

@dataclass
class Gap_004(Gap):
    uid: str = "GAP-004"
    requirement_uid: str = "REQ-NICE-ECON-001"
    
    econ_model_claim: str = "CLAIM-013"

    def __post_init__(self):
        self.claim_uids = [self.econ_model_claim]

    def severity_score(self, conn) -> tuple:
        score = 2 # GAP_SEVERITY_ENUM[4] == supported
        new_rationale = []
        if self.get_claim_status(conn, self.econ_model_claim) == SUPPORTED:
            score += 2
            new_rationale += [self.get_claim_statement(conn, self.econ_model_claim)] # this can be done by the relational database w/ reusing the text

        score = min(5, score)
        if len(new_rationale) == 0:
                new_rationale += ["No economic model or cost-effectiveness assumptions included"]

        return (GAP_SEVERITY_ENUM[score], "; ".join(new_rationale))

@dataclass
class Gap_005(Gap):
    uid: str = "GAP-005"
    requirement_uid: str = "REQ-US-BIOMARKER-001"
    
    biomarker_claim: str = "CLAIM-005"

    def __post_init__(self):
        self.claim_uids = [self.biomarker_claim]

    def severity_score(self, conn) -> tuple:
        score = 2 # GAP_SEVERITY_ENUM[4] == supported
        new_rationale = []
        if self.get_claim_status(conn, self.biomarker_claim) == SUPPORTED:
            score += 2
            new_rationale += [self.get_claim_statement(conn, self.biomarker_claim)] # this can be done by the relational database w/ reusing the text

        score = min(5, score)
        if len(new_rationale) == 0:
                new_rationale += ["Biomarker is either not included, not well defined, or not useful."]

        return (GAP_SEVERITY_ENUM[score], "; ".join(new_rationale))

@dataclass
class Gap_006(Gap):
    uid: str = "GAP-006"
    requirement_uid: str = "REQ-US-BIOMARKER-001"
    
    biomarker_effective_claim: str = "CLAIM-005"
    biomarker_testing_path_claim: str = "CLAIM-014"
    subgroup_claim: str = "CLAIM-015"

    def __post_init__(self):
        self.claim_uids = [self.biomarker_effective_claim, self.biomarker_testing_path_claim, self.subgroup_claim]

    def severity_score(self, conn) -> tuple:
        score = 1 # GAP_SEVERITY_ENUM[-1] == supported
        new_rationale = []
        if self.get_claim_status(conn, self.biomarker_effective_claim) == SUPPORTED:
            score += 1
            new_rationale += ["VER-101 addresses unmet need in a biomarker-defined NSCLC population."] # this can be done by the relational database w/ reusing the text
        else:
                new_rationale += ["Relevant and well defined biomarker is not present"]

        if self.get_claim_status(conn, self.biomarker_testing_path_claim) == SUPPORTED:
            score += 1
            new_rationale += ["VER-101 biomarker testing pathway is well defined."] # this can be done by the relational database w/ reusing the text
        else:
                new_rationale += ["Biomarker testing pathway is not defined"]

        if self.get_claim_status(conn, self.subgroup_claim) == SUPPORTED:
            score += 1
            new_rationale += ["VER-101 has rigorous statistically analysis subgroups."] # this can be done by the relational database w/ reusing the text
        else:
                new_rationale += ["Subgroups are not rigorously analyzed"]

        score = min(5, score)
        # GAP_SEVERITY_ENUM = ("unknown", "big", "not sufficient", "near sufficient", "sufficient", "exceeding"))
        return (GAP_SEVERITY_ENUM[score], "; ".join(new_rationale))

GAP_REGISTRY: dict[str, type[Gap]] = {
    cls.__dataclass_fields__['uid'].default: cls
    for cls in Gap.__subclasses__()
}
