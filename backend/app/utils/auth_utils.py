from app.config import Settings
from fastapi import Header, HTTPException
from jose import jwt, JWTError

settings = Settings() # type: ignore

def get_user_id(authorization: str | None = Header(default=None)) -> str:
    """Gets current user ID."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorisation header")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return payload["sub"]
