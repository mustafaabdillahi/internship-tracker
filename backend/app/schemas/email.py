from app.models.enums import ApplicationStage
from datetime import datetime
from pydantic import BaseModel

class EmailRead(BaseModel):
    id: int
    subject: str | None = None
    sender: str | None = None
    received_at: datetime
    html_body: str | None = None
    text_body: str | None = None
