from app.models.enums import ApplicationStage, DeadlineType, InterviewType
from datetime import datetime
from pydantic import BaseModel, Field

class ExtractedEmail(BaseModel):
    status: ApplicationStage
    company: str | None
    company_raw: str | None
    role: str | None
    locatioon: str | None
    deadline: datetime | None
    deadline_type: DeadlineType | None
    interview_date: datetime | None
    interview_type: InterviewType | None
    next_action: str | None
    notes: str | None
    confidence: float = Field(ge=0, le=1)
    evidence: str | None


class ClassifiedEmail(BaseModel):
    is_relevant: bool
    confidence: float = Field(ge=0, le=1)
