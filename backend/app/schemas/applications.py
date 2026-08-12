from datetime import datetime
from models.models import ApplicationStage
from pydantic import BaseModel

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

