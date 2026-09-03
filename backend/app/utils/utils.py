from app.config import Settings
from app.models.ai_models import ClassifiedEmail, ExtractedEmail
from app.models.database_models import Company, CompanyAlias, EmailProcessing, EmailRecord, User
from app.models.enums import ProcessingStatus
from app.utils import application_utils, common_utils
from datetime import datetime, timezone
from googleapiclient import discovery
from google.oauth2.credentials import Credentials
from pathlib import Path
from sqlalchemy import func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from typing import Any, Mapping
import base64
import json
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

settings = Settings() # type: ignore

def create_google_user(google_user: Mapping[str, Any], refresh_token: str, db: Session) -> User:
    """Adds a user from a Google account to the user table in database. Returns the user object."""
    user_id = common_utils.generate_id(8)
    user = User(
        id=user_id,
        firstname=google_user.get("given_name"),
        surname=google_user.get("family_name"),
        email=google_user.get("email"),
        google_refresh_token=refresh_token
    )

    db.add(user)

    return user


def extract_body(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """HELPER FUNCTION: Recursively extracts human-readable body from Gmail MIME payload."""

    plain_text = None
    html = None

    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})
    data = body.get("data")

    if data:
        decoded_data = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        if mime_type == "text/plain":
            plain_text = decoded_data
        elif mime_type == "text/html":
            html = decoded_data

    # Recursively extract from parts key
    for part in payload.get("parts", []):
        part_plain, part_html = extract_body(part)
        if plain_text is None and part_plain is not None:
            plain_text = part_plain
        if html is None and part_html is not None:
            html = part_html

    return plain_text, html


def get_emails(credentials: Credentials, limit: int = 50, dump_json: bool = False) -> dict[str, dict[str, Any]]:
    """Returns the user's most recent emails."""
    service = discovery.build("gmail", "v1", credentials=credentials)
    result = service.users().messages().list(
        userId="me",
        maxResults=limit,
         q="-from:me"
    ).execute()

    messages = result.get("messages", [])
    emails = {}

    for msg in messages:
        text = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        payload = text["payload"]

        try:
            headers = {
                h["name"].lower(): h["value"]
                for h in payload.get("headers", {})
            }

            subject = headers.get("subject")
            sender = headers.get("sender") or headers.get("from")
            recipient = headers.get("delivered-to")
            received_at = datetime.fromtimestamp(
                int(text["internalDate"]) / 1000,
                tz=timezone.utc
            )

            body_text, body_html = extract_body(payload)
            emails[msg["id"]] = {
                "subject": subject,
                "sender": sender,
                "recipient": recipient,
                "thread_id": text["threadId"],
                "received-at": received_at,
                "text": body_text,
                "html": body_html
            }
            
        except Exception as e:
            print(f"Failed to process email {msg['id']}: {e}")

    if dump_json:
        dump_emails_into_json(emails)

    return emails


def dump_emails_into_json(emails: dict[str, dict[str, Any]]):
    """Dumps retrieved emails into a JSON email (FOR TESTING ONLY)."""
    json_filepath = Path(__file__).parents[2] / "test_emails.json"
    with open(json_filepath, "w+") as file:
        json.dump(emails, file, default=str, indent=4)


def write_email_records(emails: dict[str, dict[str, Any]], user: User, db: Session) -> int:
    """Writes fetched emails to email record table in database. Returns the number of records inserted."""
    records = []
    for id, email in emails.items():
        records.append({
            "provider": "gmail",
            "provider_message_id": id,
            "provider_thread_id": email["thread_id"],
            "user_id": user.id,
            "sender": email["sender"],
            "recipient": user.email,
            "subject": email["subject"],
            "received_at": email["received-at"],
            "raw_text": email["text"],
            "raw_html": email["html"]
        })

    query = postgresql.insert(EmailRecord).values(records).on_conflict_do_nothing(
        index_elements=[EmailRecord.provider, EmailRecord.provider_message_id]
    )
    result = db.execute(query)

    return result.rowcount #type: ignore


def write_processed_email_record(classified: ClassifiedEmail | None, extracted: ExtractedEmail | None, email_id: int, user_id: str, date_applied: datetime, db: Session):
    """Writes a processed email record to database."""
    process_id = common_utils.generate_id(36)
    process_obj = EmailProcessing(
        id=process_id,
        email_id=email_id,
        user_id=user_id,
        status=ProcessingStatus.COMPLETED,
        classifier_version=settings.ai_classifier_version
    )

    if classified is not None:
        process_obj.is_relevant = classified.is_relevant
        process_obj.classifier_confidence = classified.confidence
    else:
        process_obj.is_relevant = False
        process_obj.classifier_confidence = 1.0

    if extracted is not None:
        process_obj.extractor_confidence = extracted.confidence
        process_obj.extractor_evidence = extracted.evidence
        process_obj.extractor_version = settings.ai_extractor_version
        process_obj.company_raw = extracted.company_raw
        process_obj.role_raw = extracted.role

    db.add(process_obj)
    db.flush()

    # Add application if email was extracted
    if extracted is not None:
        company_id = get_company(extracted, db)
        application_utils.update_application(process_obj, extracted, company_id, date_applied, db)
        

def get_company(extracted: ExtractedEmail, db: Session) -> str:
    """Gets the company ID from extracted email.
    If it doesn't exist, creates a new company record and returns its ID."""
    # TODO: Add fuzzy matching across company/company alias rows

    company = db.query(CompanyAlias).filter(
        func.lower(CompanyAlias.alias) == func.lower(extracted.company_raw)
    ).first()

    if company is not None:
        company_id = company.company_id
    else:
        normalised_company_name = normalise_company_name(extracted.company_raw)
        company = db.query(CompanyAlias).filter(
            func.lower(CompanyAlias.alias) == func.lower(normalised_company_name)
        ).first()

        if company is not None:
            company_id = company.company_id
        else:
            # Create new company record and alias record
            company_id = common_utils.generate_id(8)
            company = Company(
                id=company_id,
                name=normalised_company_name
            )
            db.add(company)

        alias = CompanyAlias(
            company_id=company_id,
            alias=normalised_company_name
        )
        db.add(alias)

    return company_id


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
