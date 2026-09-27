from pydantic import BaseModel

class OAuthCodeRequest(BaseModel):
    code: str
