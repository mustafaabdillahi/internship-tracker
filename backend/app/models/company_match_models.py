from app.models.database_models import Company
from dataclasses import dataclass
from enum import Enum

class MatchOutcome(Enum):
    CONFIDENT = "confident"
    AMBIGUOUS = "ambiguous"
    NO_MATCH_CREATE_NEW = "no_match_create_new"
    NO_MATCH_FLAG = "no_match_flag"

@dataclass
class MatchResult:
    outcome: MatchOutcome
    company: Company | None
    candidates: list["ScoredCandidate"]
    reason: str
    should_create: bool = False

@dataclass
class ScoredCandidate:
    company: Company
    matched_alias: str
    ratio_score: float
    token_sort_score: float
    total_score: float