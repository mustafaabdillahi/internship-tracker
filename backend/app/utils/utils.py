from app.models.models import User, EmailRecord
from datetime import datetime, timezone
from googleapiclient import discovery
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session
from typing import Any, Mapping
import base64
import secrets
import string

characters = string.ascii_letters + string.digits

def create_google_user(google_user: Mapping[str, Any], refresh_token: str, db: Session) -> User:
    """Adds a user from a Google account to the user table in database. Returns the user object."""
    user_id = "".join(secrets.choice(characters) for _ in range(8))
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
            part_html = part_html

    return plain_text, html


def get_emails(credentials: Credentials, limit: int = 20) -> dict[str, dict[str, str]]:
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
            sender = headers.get("sender")
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
                "received-at": received_at,
                "text": body_text,
                "html": body_html
            }
            
        except Exception as e:
            print(f"Failed to process email {msg['id']}: {e}")

    return emails


def write_email_records(emails: dict[str, dict[str, str]], user: User, db: Session):
    """Writes fetched emails to email record table in database."""

    for id, email in emails.items():
        record = EmailRecord(
            id=id,
            sender=email["sender"],
            recipient=user.email,
            subject=email["subject"],
            received_at=email["received-at"],
            raw_text=email["text"],
            raw_html=email["html"]
        )
        db.add(record)