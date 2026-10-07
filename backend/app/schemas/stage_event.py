from app.models.enums import ApplicationStage
from datetime import datetime
from pydantic import BaseModel

class StageEventRead(BaseModel):
    id: str
    stage: ApplicationStage
    created_at: datetime
