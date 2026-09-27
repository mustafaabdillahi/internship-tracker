from app.config import Settings
settings = Settings() # type: ignore

if not settings.production:
    import os
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from app.ai import classifier, email_pruner, extractor
from app.database import SessionLocal
from app.models.database_models import Application, Company, CompanyAlias, EmailProcessing, EmailRecord, StageEvent, User
from app.schemas.application import ApplicationCreateFrontend, ApplicationRead, ApplicationUpdate
from app.schemas.auth import OAuthCodeRequest
from app.schemas.user import UserRead
from app.utils import application_utils, auth_utils, common_utils, utils
from datetime import date, datetime, time, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from jose import jwt
from sqlalchemy.dialects import postgresql
import secrets
import sqlalchemy
import sqlalchemy.exc


app = FastAPI()
engine = sqlalchemy.create_engine(settings.psql_url)

oauth_codes: dict[str, dict] = {}

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

    oauth_code = secrets.token_urlsafe(32)
    oauth_codes[oauth_code] = {
        "user_id": user.id,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=1)
    }

    response = RedirectResponse(f"{settings.frontend_url}/auth/callback?code={oauth_code}")

    # Redirect to callback page
    return response


@app.post("/auth/exchange")
def exchange_oauth_code(data: OAuthCodeRequest):
    oauth_data = oauth_codes.get(data.code)

    if oauth_data is None:
        raise HTTPException(status_code=400, detail="Invalid OAuth code")

    if oauth_data["expires_at"] < datetime.now(timezone.utc):
        del oauth_codes[data.code]
        raise HTTPException(status_code=400, detail="OAuth code expired")

    user_id = oauth_data["user_id"]
    del oauth_codes[data.code]

    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }

    session_token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm="HS256"
    )

    return {
        "access_token": session_token
    }


# Test page used to get user information
@app.get("/auth/me", response_model=UserRead)
def auth_user_info(user_id: str = Depends(auth_utils.get_user_id)):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User no longer exists")

        return user


# FOR TESTING ONLY: Get list of emails
@app.get("/emails")
def get_user_emails(user_id: str = Depends(auth_utils.get_user_id)):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()

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
def record_user_emails(user_id: str = Depends(auth_utils.get_user_id)):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()

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
def fetch_applications(user_id: str = Depends(auth_utils.get_user_id), company: str | None = None, location: str | None = None, role: str | None = None,
                       date_from: date | None = None, date_to: date | None = None):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        query = db.query(Application).filter(Application.user_id == user_id)
        
        filters = []
        if company is not None:
            filters.append(Application.company_name.ilike(f"%{company}%"))
        if location is not None:
            filters.append(Application.loc.ilike(f"%{location}%"))
        if role is not None:
            filters.append(Application.role.ilike(f"%{role}%"))
        if date_from is not None:
            start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
            filters.append(Application.date_applied >= start)
        if date_to is not None:
            end = datetime.combine(date_to + timedelta(days=1), time.max, tzinfo=timezone.utc)
            filters.append(Application.date_applied < end)

        applications = query.filter(*filters).all()

        return [
            application_utils.get_application_read(app, db)
            for app in applications
        ]


@app.get("/applications/{application_id}", response_model=ApplicationRead)
def fetch_application(application_id: int, user_id: str = Depends(auth_utils.get_user_id)):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        application = db.query(Application).filter(
            Application.id == application_id,
            Application.user_id == user_id
        ).first()

        if application is None:
            raise HTTPException(status_code=404, detail="Application not found.")

        return application_utils.get_application_read(application, db)


@app.patch("/application/update/{application_id}", response_model=ApplicationRead)
def update_application(application_id: int, update: ApplicationUpdate, user_id: str = Depends(auth_utils.get_user_id)):
    with SessionLocal() as db:
        application = db.query(Application).filter(
            Application.id == application_id,
            Application.user_id == user_id
        ).first()

        if application is None:
            raise HTTPException(status_code=404, detail="Application not found")

        old_stage = application.stage
        update_data = update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(application, field, value)

        if update.stage is not None and update.stage != old_stage:
            stage_event = StageEvent(
                id=common_utils.generate_id(6),
                application_id=application.id,
                stage=update.stage,
                role=application.role,
                dt=datetime.now(timezone.utc)
            )
            db.add(stage_event)

        if update.company_name is not None:
            query = postgresql.insert(CompanyAlias).values(
                company_id=application.company_id,
                alias=update.company_name
            ).on_conflict_do_nothing(
                constraint="uq_company_alias"
            )
            db.execute(query)
        

        db.commit()
        db.refresh(application)

        return application_utils.get_application_read(application, db)


@app.post("/application/create")
def create_application(data: ApplicationCreateFrontend, user_id: str = Depends(auth_utils.get_user_id)) -> ApplicationRead:
    """Manually creates application."""

    with SessionLocal() as db:
        alias = db.query(CompanyAlias).filter(
            sqlalchemy.func.lower(CompanyAlias.alias) == sqlalchemy.func.lower(data.company_name)
        ).first()

        if alias is not None:
            company = db.query(Company).filter(
                Company.id == alias.company_id
            ).first()

            if company is None:
                raise sqlalchemy.exc.NoResultFound(f"Company alias {alias.alias} is orphaned")

        else:
            company = Company(
                id=common_utils.generate_id(8),
                name=data.company_name
            )
            db.add(company)
            db.flush()

            new_alias = CompanyAlias(
                company_id=company.id,
                alias=data.company_name
            )
            db.add(new_alias)
            
        application = Application(
            user_id=user_id,
            company_id=company.id,
            company_name=data.company_name,
            role=data.role,
            stage=data.stage,
            date_applied=datetime.now(timezone.utc),
            loc=data.loc,
            employment_type=data.employment_type,
            notes=data.notes
        )
        db.add(application)
        db.flush()

        stage_event = StageEvent(
            id=common_utils.generate_id(12),
            application_id=application.id,
            stage=data.stage,
            dt=datetime.now(timezone.utc)
        )
        db.add(stage_event)
        
        db.commit()
        db.refresh(application)

        return application_utils.get_application_read(application, db)


@app.delete("/application/delete/{application_id}")
def delete_application(application_id: int,  user_id: str = Depends(auth_utils.get_user_id)):
    with SessionLocal() as db:
        application = db.query(Application).filter(
            Application.id == application_id,
            Application.user_id == user_id
        ).first()

        if application is None:
            raise HTTPException(status_code=404, detail="Application not found")

        db.delete(application)
        db.commit()

    return {
        "success": f"Application id={id} deleted"
    }


@app.get("/emails/process/{email_id}")
def process_email(email_id: int, user_id: str = Depends(auth_utils.get_user_id)):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        email = db.query(EmailRecord).filter(
            EmailRecord.id == email_id,
            EmailRecord.user_id == user_id
        ).first()

        if email is None:
            raise HTTPException(status_code=404, detail="Email not found.")

        processed_email = db.query(EmailProcessing).filter(
            EmailProcessing.email_id == email_id,
            EmailProcessing.user_id == user_id
        ).first()

        # If e-mail already processed, return the stored information
        if processed_email is not None:
            return {
                "success": "Email already processed",
                "is_relevant": processed_email.is_relevant,
                "confidence": processed_email.classifier_confidence
            }

        pruned_email = email_pruner.prune_emails([email])[email_id]
        output = classifier.classify_email(pruned_email)
        if output is not None and output.is_relevant:
            extracted = extractor.extract_email(pruned_email)
        else:
            extracted = None
            
        utils.write_processed_email_record(
            output,
            extracted,
            email_id,
            user_id,
            email.received_at,
            db
        )

        db.commit()

        if output is not None and output.is_relevant:
            return {
                "success": "Processed email recorded",
                "pruned_email": pruned_email,
                "output": extracted
            }
        else:
            return {
                "success": "Processed email recorded",
                "pruned_email": pruned_email,
                "is_relevant": output.is_relevant if output is not None else False,
                "confidence": output.confidence if output is not None else 1.0
            }


@app.post("/auth/logout")
def auth_logout():
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