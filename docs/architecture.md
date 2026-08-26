# Database Schema
The schema below is expressed in DBML.
```SQL
Table user {
  id varchar [primary key]
  firstname varchar
  surname varchar
  email varchar [not null]
  created_at timestamp [not null]
}

Table application {
  id integer [primary key]
  userid varchar [not null]
  company_id varchar
  role varchar
  stage enum
  date_applied timestamp [not null]
  loc location
  employment_type varchar
  notes text
}

Table stage_event {
  id varchar [primary key]
  application_id integer [not null]
  stage enum [not null]
  dt timestamp [not null]
}

Table email_record {
  id varchar
  application_id integer
  sender varchar [not null]
  recipient varchar [not null]
  subject varchar
  received_at timestamp [not null]
  raw_text raw [not null]
  raw_html raw [not null]
  created_at timestamp [not null]
}

Table company {
  id varchar [primary key]
  name varchar [not null]
  website_url varchar
  linkedin_url varchar
  careers_url varchar
  industry varchar
  size integer
  created_at timestamp [not null]
}

Ref has_application: user.id <? application.userid
Ref has_stage_event: application.id <? stage_event.applicationid
Ref has_email_record: application.id <? email_record.applicationid
Ref for_company: application.companyid ?> company.id
```

# LLM JSON schema
Emails are evaluated by the AI in two stages: classification and extraction. First, emails are passed through GPT 5 nano to determine whether it is likely related to an immediate application status update. Emails with a high enough confidence level are then passed to the extractor model GPT 5 mini, which extracts key information.

The classifier will be based on the following schema:
```JSON
{
  "name": "email_classification",
  "description": "Classify whether an email containss a new job application status update / required candidate action or not. Provide a confidence level with this as well, between 0 and 1. Classify as relevant ONLY if the email communicates a change, confirmation, decision, or required action concerning a specific application that the candidate has already submitted. Do NOT classify as relevant if the email is, for example: advertising an  open position; inviting the candidate to apply; announcing an application submission deadline; describing a recruitment event; general careers marketing; confirming that applications are currently open, or providing generic information about the recruitment process.",
  "strict": true,
  "schema": {
    "type": "object",
    "properties": {
      "is_relevant": {
        "type": "boolean"
      },
      "confidence": {
        "type": "number",
        "minimum": 0,
        "maximum": 1
      }
    },
    "additionalProperties": false,
    "required": ["is_relevant", "confidence"]
  }
}
```

The extractor will use the following schema:
```JSON
{
  "name": "email_record_processed",
  "description": "Extracts structured information from an internship/job application status update email.",
  "strict": true,
  "schema": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "enum": [
          "APPLIED",
          "OA",
          "INTERVIEW",
          "OFFER",
          "REJECTED",
          "WITHDRAWN"
        ],
        "description": "The application status represented by this email."
      },
      "company": {
        "type": "string",
        "description": "Normalised company name. Do not include recruiting agencies, email addresses, or legal suffixes unless they are part of the commonly used company name."
      },
      "company_raw": {
        "type": ["string", "null"],
        "description": "The company name exactly or approximately as it appears in the email."
      },
      "role": {
        "type": ["string", "null"],
        "description": "Normalised role/job title, if identifiable."
      },
      "location": {
        "type": ["string", "null"],
        "description": "Normalised job location (e.g. London, United Kingdom), if given."
      },
      "deadline": {
        "type": ["string", "null"],
        "description": "Deadline by which the user must take an action. ISO 8601 datetime with timezone where available."
      },
      "deadline_type": {
        "type": ["string", "null"],
        "enum": [
          "OA",
          "APPLICATION",
          "INTERVIEW_CONFIRMATION",
          "DOCUMENT_SUBMISSION",
          "OTHER"
        ],
        "description": "What the deadline applies to."
      },
      "interview_date": {
        "type": ["string", "null"],
        "description": "Scheduled interview datetime in ISO 8601 format, if given."
      },
      "interview_type": {
        "type": ["string", "null"],
        "enum": [
          "PHONE",
          "VIDEO",
          "TECHNICAL",
          "BEHAVIORAL",
          "ASSESSMENT",
          "ONSITE",
          "OTHER"
        ],
        "description": "Type of interview, if identifiable."
      },
      "next_action": {
        "type": ["string", "null"],
        "description": "The action the candidate needs to take next, if any."
      },
      "notes": {
        "type": ["string", "null"],
        "description": "Other important information that does not fit the structured fields."
      },
      "confidence": {
        "type": "number",
        "minimum": 0,
        "maximum": 1,
        "description": "Model's estimated confidence in the overall extraction. This is a heuristic confidence score, not a calibrated probability."
      },
      "evidence": {
        "type": "string",
        "description": "Short excerpt or paraphrase identifying the key evidence supporting the extracted status."
      }
    },
    "additionalProperties": false,
    "required": [
      "status",
      "company",
      "company_raw",
      "role",
      "location",
      "deadline",
      "deadline_type",
      "interview_date",
      "interview_type",
      "next_action",
      "notes",
      "confidence",
      "evidence"
    ]
  }
}
