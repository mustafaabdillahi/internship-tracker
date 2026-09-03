from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UserRead(BaseModel):
    id: str
    firstname: str | None
    surname: str | None
    email: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )