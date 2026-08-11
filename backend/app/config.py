from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    # .env file used to load in settings
    model_config = SettingsConfigDict(
        env_file = BASE_DIR / ".env",
        env_file_encoding="utf-8"
    )

    # Settings
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    psql_database: str
    psql_password: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"postgres:{self.psql_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.psql_database}"
        )
