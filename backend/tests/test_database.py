from app.database import SessionLocal
from sqlalchemy import text

def test_database_connection():
    """Tests whether the Postgres database connection works."""
    with SessionLocal() as db:
        result = db.execute(text("SELECT 1;"))
        assert result.scalar() == 1
