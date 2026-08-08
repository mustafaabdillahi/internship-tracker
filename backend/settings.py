from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Example setting
    app_name: str = "Internship Tracker"

    # .env file used to load in settings
    model_config = SettingsConfigDict(
        env_file = "./.env",
        env_file_encoding="utf-8"
    )