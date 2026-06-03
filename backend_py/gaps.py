from dataclasses import dataclass, field, asdict
import backend_py.db as db

GAP_SEVERITY_ENUM = db.GAP_SEVERITY_ENUM
CLAIM_STATUS_ENUM = db.CLAIM_STATUS_ENUM
assert (GAP_SEVERITY_ENUM == ("unknown", "big", "not sufficient", "near sufficient", "sufficient", "exceeding"))
assert (CLAIM_STATUS_ENUM[-1] == "supported")

@dataclass
class Gap:
    # User Input
    uid: str 
    requirement_uid: str
    # Pulled from Database
    type: str
    jurisdiction: str
    # Set by Class Functions
    rationale: str
    recommended_action: str
    # defaults
    review_status: str = "unreviewed"
    severity: int = 1 # big
    claim_uids: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.jurisdiction = self.get_jurisdiction()
        self.type = self.get_type()

    def severity_score(self) -> float:
        raise NotImplementedError

    def to_dict(self) -> dict:
        return asdict(self)

    def get_claim_status(self, claim_uid) -> str:
         return "TODO: implement get_claim_status"
    def get_claim_statement(self, claim_uid) -> str:
        return "TODO: implement get_claim_statement"
    
    def get_type(self, req_uid = None) -> str:
        if req_uid is None:
            req_uid = self.requirement_uid
        return "TODO: need to implement get_type"
    def get_jurisdiction(self, req_uid = None) -> str:
        if req_uid is None:
            req_uid = self.requirement_uid
        return "TODO: need to implement get_jusridiction"


    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(uid={self.uid}, severity={self.severity})"


@dataclass
class Gap_001(Gap):
    uid: str = "GAP-001"
    type: str = "Comparator uncertainty"
    jurisdiction: str = "NICE/England"
    # severity = "big"
    rationale: str = "no randomized comparator"
    recommended_action: str = "Assess indirect comparison feasibility and RWE augmentation plan"
    requirement_uid: str = "REQ-NICE-COMP-001"

    SOC_comparator_claim: str = "CLAIM-006"
    direct_comparator_claim: str = "CLAIM-007"
    placebo_comparator_claim: str = "CLAIM-008"
    indirect_comparator_claim: str = "CLAIM-009"

    def __post_init__(self):
        # super().__post_init__() TODO use parent auto set funcs
        self.claim_uids = [self.SOC_comparator_claim, self.direct_comparator_claim, self.placebo_comparator_claim, self.indirect_comparator_claim]

    def severity_score(self) -> tuple:
        score = 1 # GAP_SEVERITY_ENUM[4] == supported
        new_rationale = ""
        # If standard-of-care comparator is present
        if not (self.get_claim_status(self.SOC_comparator_claim) == CLAIM_STATUS_ENUM[-1]):
            score += 2
            new_rationale += "Standard of Care comparator is present; "

        if not (self.get_claim_status(self.placebo_comparator_claim) == CLAIM_STATUS_ENUM[-1]):
            score += 1
            new_rationale += "Placebo comparator is present; "

        if not (self.get_claim_status(self.direct_comparator_claim) == CLAIM_STATUS_ENUM[-1]):
            score += 1
            new_rationale += "Direct comparator is present; "

        if not (self.get_claim_status(self.indirect_comparator_claim) == CLAIM_STATUS_ENUM[-1]):
            score += 1
            new_rationale += "Indirect comparator is present; "

        score = min(5, score)
        if len(new_rationale) == 0:
                new_rationale = "no randomized comparator"
                
        return (GAP_SEVERITY_ENUM[score], new_rationale)

@dataclass
class Gap_002(Gap):
    uid: str = "GAP-002"
    type: str = "endpoint maturity"
    jurisdiction: str = "U.S. payer archetype"
    # severity = "big"
    rationale: str = "EO-006: OS immature; EO-004: ORR primary"
    recommended_action: str = "Track longer follow-up; define durability evidence plan."
    requirement_uid: str = "REQ-US-ENDPT-001"
    
    orr_claim: str = "CLAIM-001"
    pfs_claim: str = "CLAIM-002"
    os_claim: str = "CLAIM-010"

    def __post_init__(self):
        # super().__post_init__() TODO use parent autoset funcs
        self.claim_uids = [self.orr_claim, self.pfs_claim, self.os_claim]

    def severity_score(self) -> tuple:
        score = 1 # GAP_SEVERITY_ENUM[4] == supported
        new_rationale = []
        if not (self.get_claim_status(self.os_claim) == CLAIM_STATUS_ENUM[-1]):
            score += 3
            new_rationale += ["Overall Survival is shown"]

        if not (self.get_claim_status(self.pfs_claim) == CLAIM_STATUS_ENUM[-1]):
            score += 2
            new_rationale += ["Significant progression free survival is shown"]

        if not (self.get_claim_status(self.orr_claim) == CLAIM_STATUS_ENUM[-1]):
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
        super().__post_init__()
        self.claim_uids = [self.QoL_claim, self.PRO_claim, self.safety_and_convenience_claim]

    def severity_score(self) -> tuple:
        score = 1 # GAP_SEVERITY_ENUM[4] == supported
        new_rationale = []
        if self.get_claim_status(self.QoL_claim) == CLAIM_STATUS_ENUM[-1]:
            score += 2
            new_rationale += [self.get_claim_statement(self.QoL_claim)] # this can be done by the relational database w/ reusing the text

        if  self.get_claim_status(self.PRO_claim) == CLAIM_STATUS_ENUM[-1]:
            score += 2
            new_rationale += [self.get_claim_statement(self.PRO_claim)]

        if self.get_claim_status(self.safety_and_convenience_claim) == CLAIM_STATUS_ENUM[-1]:
            score += 1
            new_rationale += [self.get_claim_statement(self.safety_and_convenience_claim)]

        score = min(5, score)
        if len(new_rationale) == 0:
                new_rationale += ["No QoL changes or PROs supporting VER-101"]

        return (GAP_SEVERITY_ENUM[score], "; ".join(new_rationale))

@dataclass
class Gap_004(Gap):
    uid: str = "GAP-003"
    requirement_uid: str = "REQ-NICE-ECON-001"
    
    econ_model_claim: str = "CLAIM-013"

    def __post_init__(self):
        super().__post_init__()
        self.claim_uids = [self.econ_model_claim]

    def severity_score(self) -> tuple:
        score = 2 # GAP_SEVERITY_ENUM[4] == supported
        new_rationale = []
        if self.get_claim_status(self.econ_model_claim) == CLAIM_STATUS_ENUM[-1]:
            score += 2
            new_rationale += [self.get_claim_statement(self.econ_model_claim)] # this can be done by the relational database w/ reusing the text

        score = min(5, score)
        if len(new_rationale) == 0:
                new_rationale += ["No economic model or cost-effectiveness assumptions included"]

        return (GAP_SEVERITY_ENUM[score], "; ".join(new_rationale))

@dataclass
class Gap_005(Gap):
    uid: str = "GAP-003"
    requirement_uid: str = "REQ-US-BIOMARKER-001"
    
    biomkr_claim: str = "CLAIM-005"

    def __post_init__(self):
        super().__post_init__()
        self.claim_uids = [self.biomkr_claim]

    def severity_score(self) -> tuple:
        score = 2 # GAP_SEVERITY_ENUM[4] == supported
        new_rationale = []
        if self.get_claim_status(self.biomkr_claim) == CLAIM_STATUS_ENUM[-1]:
            score += 2
            new_rationale += [self.get_claim_statement(self.biomkr_claim)] # this can be done by the relational database w/ reusing the text

        score = min(5, score)
        if len(new_rationale) == 0:
                new_rationale += ["Biomarker is either not included, not well defined, or not useful."]

        return (GAP_SEVERITY_ENUM[score], "; ".join(new_rationale))

@dataclass
class Gap_006(Gap):
    uid: str = "GAP-003"
    requirement_uid: str = "REQ-US-BIOMARKER-001"
    
    biomkr_effective_claim: str = "CLAIM-005"
    biomrk_testing_path_claim: str = "CLAIM-014"
    subgroup_claim: str = "CLAIM-015"

    def __post_init__(self):
        super().__post_init__()
        self.claim_uids = [self.biomkr_effective_claim, self.biomrk_testing_path_claim, self.subgroup_claim]

    def severity_score(self) -> tuple:
        score = 1 # GAP_SEVERITY_ENUM[-1] == supported
        new_rationale = []
        if self.get_claim_status(self.biomkr_effective_claim) == CLAIM_STATUS_ENUM[-1]:
            score += 1
            new_rationale += [self.get_claim_statement(self.biomkr_effective_claim)] # this can be done by the relational database w/ reusing the text
        else:
             new_rationale += ["Relevant and well defined biomarker is not present"]

        if self.get_claim_status(self.biomrk_testing_path_claim) == CLAIM_STATUS_ENUM[-1]:
            score += 1
            new_rationale += [self.get_claim_statement(self.biomrk_testing_path_claim)] # this can be done by the relational database w/ reusing the text
        else:
             new_rationale += ["Biomarker testing pathway is not defined"]

        if self.get_claim_status(self.subgroup_claim) == CLAIM_STATUS_ENUM[-1]:
            score += 1
            new_rationale += [self.get_claim_statement(self.subgroup_claim)] # this can be done by the relational database w/ reusing the text
        else:
             new_rationale += ["Subgroups are not rigorously analyzed"]

        score = min(5, score)

        return (GAP_SEVERITY_ENUM[score], "; ".join(new_rationale))