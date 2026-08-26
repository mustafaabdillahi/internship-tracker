from app.ai.email_pruner import prune_emails
from app.config import Settings
from app.models.ai_models import ClassifiedEmail
from app.models.database_models import EmailRecord
from openai import OpenAI

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


def classify_email(email: EmailRecord) -> ClassifiedEmail | None:
    """Uses AI to classify a pruned email as to whether it is an internship status update."""

    pruned = prune_emails([email])[email.id]

    # If text is empty/null, do not call AI at all
    if pruned["text"] is None or len(pruned["text"]) == 0:
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
                "content": str(pruned)
            }
        ],
        text_format=ClassifiedEmail
    )

    return response.output_parsed
