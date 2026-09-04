from app.models.ai_models import ExtractedEmail
from app.models.database_models import Application, EmailProcessing, ManualReviewItem, StageEvent
from app.models.enums import ApplicationStage, ManualReviewType
from app.models.application_match_models import MatchOutcome, MatchResult, ScoredCandidate
from app.utils import common_utils
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import re

ROLE_RE = re.compile(r"[^a-z0-9\s]")
STOPWORDS = {"intern", "internship", "the", "a", "an", "co-op", "coop", "position", "role"}
SEASON_WORDS = {"summer", "fall", "autumn", "winter", "spring", "2025", "2026", "2027", "2028"}

STAGE_ORDER = [
    ApplicationStage.APPLIED,
    ApplicationStage.OA,
    ApplicationStage.INTERVIEW,
    ApplicationStage.OFFER,
    ApplicationStage.REJECTED,
    ApplicationStage.WITHDRAWN
]

BASE_WEIGHTS = {"role": 0.60, "recency": 0.15, "stage": 0.25}
CONFIDENT_THRESHOLD = 0.55
AMBIGUITY_GAP = 0.12

def update_application(email: EmailProcessing, extracted: ExtractedEmail, company_id: str, date_applied: datetime, db: Session) -> Application | None:
    """Creates an application if new, or updates an existing one."""
    match_result = find_matching_application(email, extracted, company_id, db)

    if match_result.application is None:
        if match_result.should_create:
            application = write_application(email, extracted, company_id, date_applied, db)
        else:
            flag_for_manual_review(email, extracted, company_id, match_result.reason, db)
            return None

    else:
        # Set status of application
        application = match_result.application
        application.stage = extracted.status

        # Backfill role and location if it didn't exist before
        if application.role is None and extracted.role:
            application.role = extracted.role
        if application.loc is None and extracted.location:
            application.loc = extracted.location

    # Write stage event
    write_stage_event(application, email, extracted, date_applied, db)

    return application


def write_stage_event(application: Application, email: EmailProcessing, extracted: ExtractedEmail, date_applied: datetime, db: Session):
    """Writes new stage event to database."""
    # TODO: Deadlines are often nonsensical, e.g. year 3333. Fix this.

    stage_event_id = common_utils.generate_id(12)
    stage_event = StageEvent(
        id=stage_event_id,
        application_id=application.id,
        stage=extracted.status,
        processing_id=email.id,
        dt=date_applied,
        deadline=extracted.deadline,
        deadline_type=extracted.deadline_type,
        interview_date=extracted.interview_date,
        interview_type=extracted.interview_type,
        notes=extracted.notes
    )
    db.add(stage_event)


def write_application(email: EmailProcessing, extracted: ExtractedEmail, company_id: str, date_applied: datetime, db: Session) -> Application:
    """Writes new application to database."""
    application = Application(
        user_id=email.user_id,
        company_id=company_id,
        role=extracted.role,
        stage=extracted.status,
        date_applied=date_applied,
        loc=extracted.location
    )
    db.add(application)
    db.flush()

    return application

def normalise_role(raw: str) -> set[str]:
    """Normalises a role name."""
    text = ROLE_RE.sub(" ", raw.lower())
    tokens = set(text.split())
    return tokens - STOPWORDS - SEASON_WORDS


def role_similarity(role_a: str | None, role_b: str | None) -> float | None:
    """Performs a Jaccard similarity on given normalised roles, from 0 to 1."""
    if not role_a or not role_b:
        return None

    a = normalise_role(role_a)
    b = normalise_role(role_b)
    if not a or not b:
        return None
    
    return len(a & b) / len(a | b)


def get_candidate_applications(user_id: str, company_id: str, db: Session) -> list[Application]:
    """Gets all applications for a user to a given company, sorted from most to least recent."""
    return (
        db.query(Application).filter(
            Application.user_id == user_id,
            Application.company_id == company_id
        )
        .order_by(Application.date_applied.desc())
        .all()
    )


def stage_plausibility(current_stage: ApplicationStage, incoming_stage: ApplicationStage) -> float:
    """Does it make sense for this application to receive this update?
    A rejection/offer email matching an application already at "rejected"
    or "offer" is less plausible than one still "in flight"."""
    if current_stage in {ApplicationStage.REJECTED, ApplicationStage.WITHDRAWN}:
        return 0.1 # Closed applications rarely get further updates

    try:
        current_index = STAGE_ORDER.index(current_stage)
        new_index = STAGE_ORDER.index(incoming_stage)
    except ValueError:
        return 0.5 # If stage unknown, don't penalise

    return 1.0 if new_index >= current_index else 0.4


def recency_score(date_applied: datetime | None) -> float:
    """Gets the score for the date applied, from 0 to 1. More recent applications get a higher score.
    An application that is older than one year gets 0."""
    if date_applied is None:
        return 0.5

    days_old = (datetime.now(timezone.utc) - date_applied).days
    return max(0.0, 1.0 - days_old / 365)


def score_candidates(applications: list[Application], extracted: ExtractedEmail) -> list[ScoredCandidate]:
    scored = []
    for app in applications:
        # Get scores
        role_s = role_similarity(app.role, extracted.role)
        recency_s = recency_score(app.date_applied)
        stage_s = stage_plausibility(app.stage, extracted.status)

        signals = {"recency": recency_s, "stage": stage_s}
        if role_s is not None:
            signals["role"] = role_s

        # Calculate total score based on weights of available scores
        active_weight = sum(BASE_WEIGHTS.values())
        total = sum(signals[k] * (BASE_WEIGHTS[k] / active_weight) for k in signals)

        scored.append(ScoredCandidate(app, role_s, recency_s, stage_s, total))

    return sorted(scored, key=lambda s: s.total_score, reverse=True)


def find_matching_application(email: EmailProcessing, extracted: ExtractedEmail, company_id: str, db: Session) -> MatchResult:
    candidates = get_candidate_applications(email.user_id, company_id, db)

    if not candidates:
        if extracted.status == ApplicationStage.APPLIED:
            return MatchResult(MatchOutcome.NO_MATCH_CREATE_NEW, None, [], "No prior application", should_create=True)

        # A follow-up with zero prior applications is suspicious but not impossible
        # (user started tracking mid-process, or extractor mistagged company).
        return MatchResult(
            MatchOutcome.NO_MATCH_CREATE_NEW if email.extractor_confidence and email.extractor_confidence > 0.8
            else MatchOutcome.NO_MATCH_FLAG,
            None, [], "Follow-up with no existing application",
            should_create=(email.extractor_confidence is not None and email.extractor_confidence > 0.8)
        )

    # Single-candidate fast path: (company_id, user_id) already narrows a lot.
    # Don't demand role evidence that may simply not exist — just check the
    # stage move isn't actively implausible (e.g. update on a closed application).
    if len(candidates) == 1:
        only = score_candidates(candidates, extracted)[0]
        if only.stage_plausibility_score >= 0.4:
            return MatchResult(
                MatchOutcome.CONFIDENT,
                only.application,
                [only],
                "single candidate, stage plausible" + ("" if only.role_score is not None else " (role unknown)")
            )

        return MatchResult(MatchOutcome.NO_MATCH_FLAG, None, [only], "Single candidate but implausible stage transition")


    scored = score_candidates(candidates, extracted)
    top = scored[0]

    # Multiple candidates AND nobody has usable role info: the discriminating
    # signal you actually trust is absent for everyone. A close numeric score
    # here reflects noise (recency/stage ties), not real confidence. Force
    # escalation rather than trusting the threshold at face value.
    if all(c.role_score is None for c in scored):
        resolved = llm_disambiguate(email, extracted, scored[:3])
        if resolved is not None:
            return MatchResult(MatchOutcome.CONFIDENT, resolved, scored, "LLM tiebreaker, no role signal available")

        return MatchResult(
            MatchOutcome.AMBIGUOUS,
            None, scored,
            "multiple candidates, no role signal anywhere, LLM declined",
            should_create=False
        )

    if len(scored) > 1 and (top.total_score - scored[1].total_score) < AMBIGUITY_GAP and top.total_score < 0.75:
        # Close race and not overwhelmingly confident, so escalate to LLM tiebreaker
        # rather than a low-confidence rules-only guess.
        resolved = llm_disambiguate(email, extracted, scored[:3])
        if resolved is not None:
            return MatchResult(MatchOutcome.CONFIDENT, resolved, scored, "LLM tiebreaker")

        return MatchResult(MatchOutcome.AMBIGUOUS, None, scored, "Ambiguous, LLM declined", should_create=False)

    if top.total_score >= CONFIDENT_THRESHOLD:
        reason = "top score above threshold" + ("" if top.role_score is not None else " (role unknown, other signals only)")
        return MatchResult(MatchOutcome.CONFIDENT, top.application, scored, reason)
    else:
        return MatchResult(MatchOutcome.NO_MATCH_FLAG, None, scored, "No candidate scored high enough")


def flag_for_manual_review(email: EmailProcessing, extracted: ExtractedEmail, company_id: str, reason: str, db: Session):
    db.add(ManualReviewItem(
        email_id=email.id,
        reason=reason,
        review_type=ManualReviewType.APPLICATION_MATCH,
        candidates={
            c.application.id: c.total_score
            for c in score_candidates(
                get_candidate_applications(email.user_id, company_id, db), extracted
            )
        }
    ))


def llm_disambiguate(email: EmailProcessing, extracted: ExtractedEmail, candidates: list[ScoredCandidate]):
    # TODO: TO BE IMPLEMENTED
    return
