# Database Schema
The schema below is expressed in DBML.
```SQL
Table user {
  id varchar [primary key]
  firstname varchar
  surname varchar
  email varchar [not null]
  password_hash varchar [not null]
  created_at timestamp [not null]
}

Table application {
  id integer [primary key]
  userid varchar [not null]
  companyid varchar
  role string
  stage string
  date_applied timestamp [not null]
}

Table stage_event {
  applicationid integer [primary key]
  stage string [primary key]
  dt timestamp [not null]
}

Table email_record {
  applicationid integer [primary key]
  recordid integer [primary key]
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