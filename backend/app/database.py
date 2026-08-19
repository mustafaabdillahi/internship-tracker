from app.config import Settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

settings = Settings() #type: ignore
engine = create_engine(settings.psql_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)