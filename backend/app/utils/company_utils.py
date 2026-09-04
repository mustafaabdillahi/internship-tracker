from app.models.ai_models import ExtractedEmail
from app.models.company_match_models import MatchOutcome, MatchResult, ScoredCandidate
from app.models.database_models import Company, CompanyAlias, EmailProcessing, ManualReviewItem
from app.models.enums import ManualReviewType, ProcessingStatus
from app.utils import common_utils
from datetime import datetime, timezone
from rapidfuzz import fuzz
from sqlalchemy import func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
import re
import unicodedata

LEGAL_SUFFIX_RE = re.compile(
    r"\b(llc|ltd|limited|inc|incorporated|corp|corporation|company|co|employment|plc|gmbh|ag|sa)\b",
    re.IGNORECASE,
)
RECRUITING_NOISE_RE = re.compile(
    r"\b(talent\s*acquisition|recruiting\s*team|university\s*relations|"
    r"campus\s*recruiting|careers?\s*team|people\s*team|hr\s*team|"
    r"staffing\s*team|hiring\s*team)\b",
    re.IGNORECASE,
)
PUNCTUATION_RE = re.compile(r"[^\w\s]")
WHITESPACE_RE = re.compile(r"\s+")

FUZZY_AUTO_MATCH_THRESHOLD = 92
FUZZY_REVIEW_THRESHOLD = 82
FUZZY_AMBIGUITY_GAP = 7
MIN_FUZZY_AUTO_LENGTH = 5

def get_company(extracted: ExtractedEmail, email: EmailProcessing, db: Session) -> str | None:
    """Gets the company ID from extracted email.
    If it doesn't exist, creates a new company record and returns its ID, if possible."""
    result = find_matching_company(extracted.company_raw, db)
    normalised = normalise_company_name(extracted.company_raw)

    if result.outcome == MatchOutcome.CONFIDENT:
        # Cannot safely continue until company name is resolved
        assert result.company is not None

        write_alias(result.company.id, normalised, db)
        return result.company.id

    
    # Otherwise, create company record and alias if recommended
    if result.should_create:
        company_id = common_utils.generate_id(8)
        company = Company(
            id=company_id,
            name=normalised
        )
        db.add(company)
        db.flush()

        write_alias(company_id, normalised, db)

        return company_id 

    # Otherwise, flag company for manual review
    flag_for_manual_review(result, email, db)

    return None


def normalise_company_name(name: str) -> str:
    """Normalises a company name."""
    # Remove accents
    name = "".join(
        c for c in unicodedata.normalize("NFKD", name)
        if not unicodedata.combining(c)
    )

    name = PUNCTUATION_RE.sub(" ", name)
    name = LEGAL_SUFFIX_RE.sub("", name)
    name = RECRUITING_NOISE_RE.sub("", name)
    name = WHITESPACE_RE.sub(" ", name)

    return name.strip()


def can_auto_fuzzy_match(query: str) -> bool:
    """Determines whether a company name should allow automatic fuzzy matching.
    Short names can give weird results."""
    return len(query.replace(" ","")) >= MIN_FUZZY_AUTO_LENGTH


def company_similarity(a: str, b: str) -> tuple[float, float, float]:
    a = normalise_company_name(a)
    b = normalise_company_name(b)

    ratio = fuzz.ratio(a, b)
    token_sort = fuzz.token_sort_ratio(a, b)
    score = 0.7*ratio + 0.3*token_sort

    return ratio, token_sort, score


def score_candidates(raw_name: str, db: Session) -> list[ScoredCandidate]:
    aliases = db.query(CompanyAlias).join(Company).all()
    best_by_company = {}

    for alias in aliases:
        ratio_s, token_sort_s, total_s = company_similarity(raw_name, alias.alias)
        candidate = ScoredCandidate(
            company=alias.company,
            matched_alias=alias.alias,
            ratio_score=ratio_s,
            token_sort_score=token_sort_s,
            total_score=total_s
        )

        current = best_by_company.get(alias.company_id)
        if not current or candidate.total_score > current.total_score:
            best_by_company[alias.company_id] = candidate

    return sorted(best_by_company.values(), key=lambda c: c.total_score, reverse=True)


def find_matching_company(raw_name: str, db: Session) -> MatchResult:
    normalised = normalise_company_name(raw_name)

    # Test exact normalised match first
    exact = db.query(CompanyAlias).filter(
        func.lower(CompanyAlias.alias) == func.lower(normalised)
    ).all()

    if len(exact) == 1:
        return MatchResult(
            outcome=MatchOutcome.CONFIDENT,
            company=exact[0].company,
            candidates=[],
            reason="Exact normalised alias match"
        )
    elif len(exact) > 1:
        return MatchResult(
            outcome=MatchOutcome.AMBIGUOUS,
            company=None,
            candidates=[],
            reason="Normalised alias maps to multiple companies"
        )

    # If no companies match exactly
    alias_count = db.query(CompanyAlias).count()
    if alias_count == 0:
        return MatchResult(
            outcome=MatchOutcome.NO_MATCH_CREATE_NEW,
            company=None,
            candidates=[],
            reason="No existing candidates",
            should_create=True
        )

    # If no aliases match the company at all
    candidates = score_candidates(raw_name, db)

    if not candidates:
        return MatchResult(
            outcome=MatchOutcome.NO_MATCH_CREATE_NEW,
            company=None,
            candidates=[],
            reason="No company candidates",
            should_create=True
        )

    # If there exist candidates for the company name
    top = candidates[0]
    if len(candidates) > 1:
        second = candidates[1]
        gap = top.total_score - second.total_score
    else:
        second = None
        gap = 100

    # Do not auto-fuzzy-match short names
    if not can_auto_fuzzy_match(normalised):
        if top.total_score >= FUZZY_REVIEW_THRESHOLD:
            return MatchResult(
                outcome=MatchOutcome.AMBIGUOUS,
                company=None,
                candidates=candidates,
                reason="Short company name requires manual confirmation"
            )
        else:
            return MatchResult(
                outcome=MatchOutcome.NO_MATCH_CREATE_NEW,
                company=None,
                candidates=candidates,
                reason="Short name and no exact alias",
                should_create=True
            )

    # If there is a strong, unambiguous match
    if top.total_score >= FUZZY_AUTO_MATCH_THRESHOLD and gap >= FUZZY_AMBIGUITY_GAP:
        return MatchResult(
            outcome=MatchOutcome.CONFIDENT,
            company=top.company,
            candidates=candidates,
            reason=f"Strong fuzzy match (score={top.total_score:.1f}, gap={gap:.1f})"
        )

    # If there is a plausible but unsafe match: manually review
    if top.total_score >= FUZZY_REVIEW_THRESHOLD:
        return MatchResult(
            outcome=MatchOutcome.AMBIGUOUS,
            company=None,
            candidates=candidates,
            reason=(
                f"Possible company matches requires review "
                f"(score={top.total_score:.1f}, gap={gap:.1f})"
            )
        )

    # Otherwise, nothing looks sufficiently familiar: create new company
    return MatchResult(
        outcome=MatchOutcome.NO_MATCH_CREATE_NEW,
        company=None,
        candidates=candidates,
        reason=f"No candidate is sufficiently similar (score={top.total_score:.1f})",
        should_create=True,
    )


def flag_for_manual_review(result: MatchResult, email: EmailProcessing, db: Session):
    db.add(ManualReviewItem(
        email_id=email.id,
        reason=result.reason,
        review_type=ManualReviewType.COMPANY_MATCH,
        candidate_application_ids={
            c.company.id: c.total_score 
            for c in result.candidates[:5]
        }
    ))
    email.status = ProcessingStatus.NEEDS_REVIEW


def resolve_company_review(review: ManualReviewItem, selected_id: str, db: Session):
    raw_name = review.email.company_raw
    if raw_name:
        normalised = normalise_company_name(raw_name)
        write_alias(selected_id, normalised, db)

    review.selected_id = selected_id
    review.resolution = "matched_existing"
    review.resolved = True
    review.resolved_at = datetime.now(timezone.utc)

    # TODO: Then continue processing email through application matching


def write_alias(company_id: str, alias: str, db: Session):
    """Writes company alias to database, if the company does not already have that alias."""
    stmt = postgresql.insert(CompanyAlias).values(
        company_id=company_id,
        alias=alias,
    ).on_conflict_do_nothing(
        index_elements=[CompanyAlias.company_id, CompanyAlias.alias]
    )
    db.execute(stmt)
