from googleapiclient import discovery
from google.oauth2.credentials import Credentials
from models.models import User
from sqlalchemy.orm import Session
from typing import Any, Mapping
import base64
import secrets
import string

characters = string.ascii_letters + string.digits

def create_google_user(google_user: Mapping[str, Any], refresh_token: str, db: Session) -> str:
    """Adds a user from a Google account to the user table in database. Returns user ID."""
    user_id = "".join(secrets.choice(characters) for _ in range(8))
    user = User(
        id=user_id,
        firstname=google_user.get("given_name"),
        surname=google_user.get("family_name"),
        email=google_user.get("email"),
        google_refresh_token=refresh_token
    )

    db.add(user)

    return user_id


def get_emails(credentials: Credentials, limit: int = 20) -> dict[str, dict[str, str]]:
    """Returns the user's most recent emails."""
    service = discovery.build("gmail", "v1", credentials=credentials)
    result = service.users().messages().list(userId="me", maxResults=limit).execute()
    messages = result.get("messages")
    emails = {}

    for msg in messages:
        text = service.users().messages().get(userId="me", id=msg["id"]).execute()

        try:
            payload = text["payload"]
            headers = payload["headers"]
            subject = None
            sender = None
            for d in headers:
                if d["name"] == "Subject":
                    subject = d["value"]
                if d["name"] == "From":
                    sender = d["value"]

            data = payload.get("parts")[0]["body"]["data"]
            data = data.replace("-","+").replace("_","/")
            decoded_data = base64.b64decode(data).decode("utf-8", errors="replace")
            emails[msg["id"]] = {"subject": subject, "sender": sender, "data": decoded_data}
            
        except Exception as e:
            print(f"Failed to process email {msg['id']}: {e}")

    return emails