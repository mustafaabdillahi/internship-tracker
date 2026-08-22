from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    # .env file used to load in settings
    model_config = SettingsConfigDict(
        env_file = BASE_DIR / ".env",
        env_file_encoding="utf-8"
    )

    # Environment
    production: bool = False

    # URLs
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    database_url: str | None = None

    # Other settings
    google_oauth_client_id: str
    google_oauth_client_secret: str
    google_oauth_scopes: list[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid"
    ]
    jwt_secret: str
    postgres_port: int = 5432
    psql_database: str
    psql_host: str = "postgres" # postgres in Docker, localhost for local
    psql_user: str = "postgres"
    psql_password: str

    @property
    def psql_url(self) -> str:
        if self.production and self.database_url is not None:
            return self.database_url
        else:
            return (
                f"postgresql+psycopg2://"
                f"{self.psql_user}:{self.psql_password}"
                f"@{self.psql_host}:{self.postgres_port}"
                f"/{self.psql_database}"
            )

    @property
    def google_client_config(self) -> dict[str, dict[str, str]]:
        return {"web": {
            "client_id": self.google_oauth_client_id,
            "client_secret": self.google_oauth_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }}

    @property
    def google_oauth_callback_url(self) -> str:
        return f"{self.backend_url}/auth/google/callback"
