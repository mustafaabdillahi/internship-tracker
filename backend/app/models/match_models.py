from app.models.database_models import Application
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
    application: Application | None
    candidates: list["ScoredCandidate"]
    reason: str
    should_create: bool = False

@dataclass
class ScoredCandidate:
    application: Application
    role_score: float | None
    recency_score: float
    stage_plausibility_score: float
    total_score: float
