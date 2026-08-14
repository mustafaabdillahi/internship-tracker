from config import Settings
from fastapi import FastAPI
from google_auth_oauthlib.flow import Flow
import sqlalchemy

settings = Settings() #type: ignore
app = FastAPI()
engine = sqlalchemy.create_engine(settings.database_url)

# For now, just pings the database
@app.get("/health")
def get_health():
    with engine.connect() as conn:
        query = sqlalchemy.text("SELECT 1;")
        conn.execute(query)
        conn.commit()
    return {"Database": "pinged"}

@app.get("/auth/google/login")
def login_google():
    flow = Flow.from_client_config(
        client_config=settings.google_client_config,
        scopes=settings.google_oauth_scopes
    )
    flow.redirect_uri = "http://localhost:8000/auth/google/callback"

    authorisation_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    return {"Authorisation URL": authorisation_url, "State": state}

@app.get("/auth/google/callback")
def login_google_callback():
    return {"DEBUG": "Callback completed!"}


@app.get("/")
def root():
    return {"Hello": "World"}