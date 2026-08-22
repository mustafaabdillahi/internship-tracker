from app.config import Settings
settings = Settings() # type: ignore

if not settings.production:
    import os
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from app.database import SessionLocal
from app.models.models import Application, User
from app.schemas.application import ApplicationRead
from app.schemas.user import UserRead
from app.utils import utils
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from jose import jwt, JWTError
import secrets
import sqlalchemy


app = FastAPI()
engine = sqlalchemy.create_engine(settings.psql_url)

# Allows backend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Pings the database
@app.get("/health")
def get_health():
    with engine.connect() as conn:
        query = sqlalchemy.text("SELECT 1;")
        conn.execute(query)
        conn.commit()
    return {"Database": "pinged"}


@app.get("/auth/google/login")
def login_google():
    code_verifier = secrets.token_urlsafe(64)
    flow = Flow.from_client_config(
        client_config=settings.google_client_config,
        scopes=settings.google_oauth_scopes,
        code_verifier=code_verifier
    )
    flow.redirect_uri = settings.google_oauth_callback_url

    authorisation_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    response = RedirectResponse(authorisation_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=settings.production,
        samesite="none" if settings.production else "lax"
    )
    response.set_cookie(
        key="code_verifier",
        value=code_verifier,
        httponly=True,
        secure=settings.production,
        samesite="none" if settings.production else "lax"
    )

    return response


@app.get("/auth/google/callback")
def login_google_callback(request: Request):
    # Get state and code verifier from cookies
    state = request.cookies.get("oauth_state")
    code_verifier = request.cookies.get("code_verifier")
    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state")
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Missing code verifier")

    # Get flow and credentials
    flow = Flow.from_client_config(
        client_config=settings.google_client_config,
        scopes=settings.google_oauth_scopes,
        state=state,
        code_verifier=code_verifier
    )

    flow.redirect_uri = settings.google_oauth_callback_url
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials

    # Get Google user details
    google_user = id_token.verify_oauth2_token(
        credentials.id_token, #type: ignore
        google_requests.Request(),
        settings.google_oauth_client_id
    )

    # If user not in database, create it from Google account info
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == google_user["email"]).first()
        if user is None:
            user = utils.create_google_user(
                google_user,
                credentials.refresh_token, # type: ignore
                db
            )
        else:
            # Update user's refresh token if it exists
            if credentials.refresh_token:
                user.google_refresh_token = credentials.refresh_token

        db.commit()
        db.refresh(user)

    # Declare session token
    payload = {
        "sub": user.id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    session_token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm="HS256"
    )

    # Add session token to cookies
    response = RedirectResponse(f"{settings.frontend_url}/dashboard")
    response.delete_cookie("code_verifier")
    response.delete_cookie("oauth_state")
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=settings.production,
        samesite="none" if settings.production else "lax",
        max_age=60*60*24*7 # 7 days
    )

    # Redirect back to home page
    return response


# Test page used to store user information
@app.get("/auth/me", response_model=UserRead)
def auth_user_info(request: Request):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            session,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    with SessionLocal() as db:
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User no longer exists")

        return user


# FOR TESTING ONLY: Get list of emails
@app.get("/emails")
def get_user_emails(request: Request):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = jwt.decode(
        session,
        settings.jwt_secret,
        algorithms=["HS256"]
    )

    with SessionLocal() as db:
        user = db.query(User).filter(User.id == payload["sub"]).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        if not user.google_refresh_token:
            raise HTTPException(status_code=400, detail="Google account is not connected.")

        credentials = Credentials(
            token=None,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret,
            scopes=settings.google_oauth_scopes
        )

        return utils.get_emails(credentials)


@app.post("/gmail/sync")
def record_user_emails(request: Request):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = jwt.decode(
        session,
        settings.jwt_secret,
        algorithms=["HS256"]
    )

    with SessionLocal() as db:
        user = db.query(User).filter(User.id == payload["sub"]).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        if not user.google_refresh_token:
            raise HTTPException(status_code=400, detail="Google account is not connected.")

        credentials = Credentials(
            token=None,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret,
            scopes=settings.google_oauth_scopes
        )

        emails = utils.get_emails(credentials)
        new_records = utils.write_email_records(emails, user, db)
        db.commit()
        db.refresh(user)

    return {"DEBUG": f"Success. {new_records} emails recorded."}


@app.get("/applications", response_model=list[ApplicationRead])
def fetch_applications(request: Request):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = jwt.decode(
        session,
        settings.jwt_secret,
        algorithms=["HS256"]
    )

    with SessionLocal() as db:
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        applications = db.query(Application).filter(Application.user_id == payload["sub"]).all()

        return applications


@app.get("/applications/{application_id}", response_model=ApplicationRead)
def fetch_application(request: Request, application_id: int):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = jwt.decode(
        session,
        settings.jwt_secret,
        algorithms=["HS256"]
    )

    with SessionLocal() as db:
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        application = db.query(Application).filter(
            Application.id == application_id,
            Application.user_id == payload["sub"]
        ).first()

        if application is None:
            raise HTTPException(status_code=404, detail="Application not found.")

        return application


@app.post("/auth/logout")
def auth_logout(request: Request):
    response = Response(status_code=204)
    response.delete_cookie(
        key="session",
        secure=settings.production,
        samesite="none" if settings.production else "lax",
    )

    return response


@app.get("/")
def root():
    return {"Hello": "World"}