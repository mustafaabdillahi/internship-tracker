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
When sending e-mails to the AI client, it will return data based on the following schema:

```JSON
{
  "name": "email_record_processed",
  "description": "Extracts key information to track from a job application update email",
  "strict": true,
  "schema": {
    "type": "object",
    "properties": {
      "status": {
        "type": "enum",
        "description": "The current status update",
        "enum": [
          "APPLIED",
          "OA",
          "INTERVIEW",
          "OFFER",
          "REJECTED",
          "WITHDRAWN"
        ],
        "example": "INTERVIEW"
      },
      "company": {
        "type": "string"
        "description": "The company the user is receiving a status from",
        "example": "Goldman Sachs"
      },
      "role": {
        "type": ["string", "null"],
        "description": "The normalised role name (core job title) for which the user is applying, if given",
        "example": "Software Engineer Intern"
      },
      "location": {
        "type": ["string", "null"],
        "description": "The location of the role",
        "example": "London, United Kingdom"
      },
      "deadline": {
        "type": ["string", "null"],
        "description": "The datetime deadline by which the user must do something if given, e.g. submit an OA, if given, formatted as YYYY-MM-DD HH:MM:SS+TZ",
        "example": "2026-08-22T17:45:00+04:30"
      },
      "interview_date": {
        "type": ["string", "null"],
        "description": "The datetime of the user's interview, if given, formatted as YYYY-MM-DD HH:MM:SS+TZ",
        "example": "2026-08-22T10:20:00+01:00"
      }
      "notes": {
        "type": ["string", "null"]
        "description": "Any other important information, if given",
        "example": "Interview is in-person."
      }
    },
    "additionalProperties": false,
    "required": [
      "status", "company", "rule", "location", "deadline", "interview_date", "notes"
    ]
  }
}
