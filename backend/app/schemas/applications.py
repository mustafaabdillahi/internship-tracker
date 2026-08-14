from app.models.models import ApplicationStage
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ApplicationCreate(BaseModel):
    userid: str
    company_id: str | None = None
    role: str | None = None
    date_applied: datetime
    loc: str | None = None
    employment_type: str | None = None
    notes: str | None = None

class ApplicationUpdate(BaseModel):
    company_id: str | None = None
    stage: ApplicationStage | None = None
    loc: str | None = None
    employment_type: str | None = None
    notes: str | None = None

class ApplicationRead(BaseModel):
    id: int
    company_id: str | None = None
    role: str | None = None
    stage: ApplicationStage | None = None
    date_applied: datetime
    loc: str | None
    employment_type: str | None = None
    notes: str | None = None

    model_config = ConfigDict(
        from_attributes=True
    )
