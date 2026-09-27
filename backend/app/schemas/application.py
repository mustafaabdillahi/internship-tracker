from app.models.enums import ApplicationStage
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ApplicationCreateFrontend(BaseModel):
    company_name: str
    stage: ApplicationStage
    role: str | None = None
    loc: str | None = None
    employment_type: str | None = None
    notes: str | None = None

class ApplicationCreate(BaseModel):
    userid: str
    company_id: str | None = None
    role: str | None = None
    date_applied: datetime
    loc: str | None = None
    employment_type: str | None = None
    notes: str | None = None

class ApplicationUpdate(BaseModel):
    company_name: str | None = None
    stage: ApplicationStage | None = None
    role: str | None = None
    loc: str | None = None
    employment_type: str | None = None
    notes: str | None = None

class ApplicationRead(BaseModel):
    id: int
    company_name: str | None = None
    role: str | None = None
    stage: ApplicationStage | None = None
    date_applied: datetime
    updated_at: datetime
    loc: str | None
    employment_type: str | None = None
    notes: str | None = None
