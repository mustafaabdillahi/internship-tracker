from app.config import Settings
from app.models.ai_models import ExtractedEmail
from openai import OpenAI
import tenacity

settings = Settings() # type: ignore
client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """
Extract structured information from an internship/job application email.

Classify the current application status as exactly one of:
APPLIED, OA, INTERVIEW, OFFER, REJECTED, WITHDRAWN.

Status rules:
- APPLIED: application submitted/received/confirmed.
- OA: online assessment or similar assessment requested.
- INTERVIEW: interview invited, scheduled, or confirmed.
- OFFER: employment/internship offer made.
- REJECTED: candidate explicitly rejected or not progressed.
- WITHDRAWN: application explicitly withdrawn/cancelled.

When multiple stages are mentioned, classify the CURRENT/MOST RECENT
status, not the earliest event. Prefer:
OFFER > REJECTED > WITHDRAWN > INTERVIEW > OA > APPLIED.

Extract only information supported by the email. Never invent or infer
missing company, role, location, dates, deadlines, interview types, or
candidate actions.

Company:
- Normalise the company name.
- Remove recruiting agencies, email addresses, domains, and legal suffixes
  unless genuinely part of the common name.
- company_raw should preserve the name as it appears in the email.

Role:
- Extract only the actual job function or position title.
- Remove company names, programme names, cohort years, and employment-type
  terms such as "Internship" or "Graduate Programme".
- Maximum length is 50 characters.
- Return null when the actual role cannot be identified.

Location:
- Extract the job's stated work location only.
- Normalise obvious abbreviations and location formats.
- Do not use the company headquarters, sender location, or interview location
  as the job location.
- Return null when the job location cannot be identified.

Deadline:
- Extract only deadlines requiring an action from the candidate.
- deadline_type must describe that action.
- Do not confuse interview dates with deadlines.
- Use ISO 8601 when a date/time is available.
- Never invent a timezone.

Interview:
- Extract the scheduled interview datetime when given.
- Classify the type as PHONE, VIDEO, TECHNICAL, BEHAVIORAL, ASSESSMENT,
  ONSITE, or OTHER.
- Use the most specific supported type; do not guess.

next_action:
- Describe the candidate's immediate required action.
- Return null when no action is required.

notes:
- Include only important information not represented elsewhere.

evidence:
- Provide a short excerpt or paraphrase supporting the selected status.

confidence:
- Return a heuristic score from 0 to 1.
- High confidence requires explicit, unambiguous evidence.
- Lower confidence when the status or extracted fields require inference.

For missing information, return null where permitted.

Return ONLY JSON conforming to the supplied schema.
"""

@tenacity.retry(
    wait=tenacity.wait_random_exponential(min=1, max=5),
    stop=tenacity.stop_after_attempt(5)
)
def extract_email(email: dict[str, str] | None) -> ExtractedEmail | None:
    """Uses AI to extract key information from a pruned email."""
    if email is None:
        return None

    response = client.responses.parse(
        model=settings.ai_extractor_model,
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
        text_format=ExtractedEmail
    )
    
    return response.output_parsed
