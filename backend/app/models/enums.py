from enum import Enum

class ApplicationStage(str, Enum):
    APPLIED = "applied"
    OA = "oa"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DeadlineType(str, Enum):
    OA = "oa"
    APPLICATION = "application"
    INTERVIEW_CONFIRMATION = "interview_confirmation"
    DOCUMENT_SUBMISSION = "document_submission"
    OTHER = "other"

class InterviewType(str, Enum):
    PHONE = "phone"
    VIDEO = "video"
    TECHNICAL = "technical"
    BEHAVIOURAL = "behavioural"
    ASSESSMENT = "assessment"
    ONSITE = "onsite"
    OTHER = "other"