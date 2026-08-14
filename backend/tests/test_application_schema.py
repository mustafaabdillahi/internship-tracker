from app.database import SessionLocal
from app.models.models import Application
from app.schemas.applications import ApplicationRead
from sqlalchemy import select

def test_applicaton_can_be_read_from_database():
    """Tests whether an application object can be read from the Postgres database."""

    db = SessionLocal()
    statement = select(Application).where(
        Application.id == 2
    )

    result = db.execute(statement)
    application = result.scalar_one_or_none()
    application_read = ApplicationRead.model_validate(application)
    data = application_read.model_dump()
    db.close()

    assert data["notes"] == "this is a test"
