from app.config import Settings
from app.models.ai_models import ClassifiedEmail
from openai import OpenAI
import tenacity

settings = Settings() # type: ignore
client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """
Classify whether an email contains a new job application status update
or required candidate action.

A relevant email must communicate a change, confirmation, decision,
or required action concerning a specific application that the candidate
has already submitted.

Do NOT classify as relevant if the email is:
- advertising an open position
- inviting the candidate to apply
- announcing an application deadline
- describing a recruitment event
- general careers marketing
- confirming that applications are currently open
- providing generic information about recruitment

Return a confidence score between 0 and 1.
"""


@tenacity.retry(
    wait=tenacity.wait_random_exponential(min=1, max=5),
    stop=tenacity.stop_after_attempt(5)
)
def classify_email(email: dict[str, str]) -> ClassifiedEmail | None:
    """Uses AI to classify a pruned email as to whether it is an internship status update."""
    # If text is empty/null, do not call AI at all
    if email["text"] is None or len(email["text"]) == 0:
        return None

    response = client.responses.parse(
        model=settings.ai_classifier_model,
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": str(email)
            }
        ],
        text_format=ClassifiedEmail
    )

    return response.output_parsed
