from dataclasses import dataclass, field, asdict

GAP_SEVERITY_ENUM: tuple = ("unknown", "big", "not sufficient", "near sufficient", "sufficient", "exceeding")

@dataclass
class Gap:
    uid: str
    type: str
    jurisdiction: str
    # review_status: str
    rationale: str
    recommended_action: str
    requirement_uid: str
    severity: int = 1
    claim_uids: list[str] = field(default_factory=list)
    # SEVERITY_ENUM: list = ["unknown", "big", "not sufficient", "near sufficient", "sufficient", "exceeding"]

    def severity_score(self) -> float:
        raise NotImplementedError

    def to_dict(self) -> dict:
        return asdict(self)

    def get_claim_status(self, claim) -> str:
         return "not implemented"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(uid={self.uid}, severity={self.severity})"


@dataclass
class Gap_001(Gap):
    uid: str = "GAP-001"
    type: str = "Comparator uncertainty"
    jurisdiction: str = "NICE/England"
    rationale: str = "no randomized comparator"
    recommended_action: str = "Assess indirect comparison feasibility and RWE augmentation plan"
    requirement_uid: str = "REQ-NICE-COMP-001"
    claim_uids: list[str] = field(default_factory=lambda: ["CLAIM-001"])

    SOC_comparator_claim: str = "CLAIM-006"
    direct_comparator_claim: str = "CLAIM-007"
    placebo_comparator_claim: str = "CLAIM-008"
    indirect_comparator_claim: str = "CLAIM-009"

def severity_score(self) -> str:
        if self.get_claim_status(self.SOC_comparator_claim) is "supported":
             return GAP_SEVERITY_ENUM[-2]
        return GAP_SEVERITY_ENUM[0]
