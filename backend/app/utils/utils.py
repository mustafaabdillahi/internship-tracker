from models.models import User
from sqlalchemy.orm import Session
from typing import Any, Mapping
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
    db.commit()
    db.refresh(user)

    return user_id