from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    # .env file used to load in settings
    model_config = SettingsConfigDict(
        env_file = "./.env",
        env_file_encoding="utf-8"
    )

    # Settings
    database_url: str = ""
