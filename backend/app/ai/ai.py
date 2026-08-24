from app.config import Settings
from openai import OpenAI

settings = Settings() # type: ignore
client = OpenAI(api_key=settings.openai_api_key)

response = client.responses.create(
    model="", # From settings
    input=""
)
