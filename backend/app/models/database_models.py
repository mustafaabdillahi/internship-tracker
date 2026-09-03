from app.models.enums import ApplicationStage, DeadlineType, InterviewType, ProcessingStatus
from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum as SQLAlchemyEnum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    firstname: Mapped[str | None] = mapped_column(String(30))
    surname: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)

    # TODO: Encrypt before production
    google_refresh_token: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    email_processings: Mapped[list["EmailProcessing"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    email_records: Mapped[list["EmailRecord"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Application(Base):
    __tablename__ = "application"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(8), ForeignKey("user.id"), nullable=False)
    company_id: Mapped[str] = mapped_column(String(8), ForeignKey("company.id"), nullable=False)
    role: Mapped[str | None] = mapped_column(String(50))
    stage: Mapped[ApplicationStage] = mapped_column(SQLAlchemyEnum(ApplicationStage), nullable=False)
    date_applied: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    loc: Mapped[str | None] = mapped_column(String(255))
    employment_type: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(
        back_populates="applications"
    )

    company: Mapped["Company | None"] = relationship(
        back_populates="applications",
    )

    stage_events: Mapped[list["StageEvent"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="StageEvent.dt"
    )

    threads: Mapped[list["ApplicationThread"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan"
    )


class StageEvent(Base):
    __tablename__ = "stage_event"

    id: Mapped[str] = mapped_column(String(12), primary_key=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("application.id"), nullable=False)
    stage: Mapped[ApplicationStage] = mapped_column(SQLAlchemyEnum(ApplicationStage), nullable=False)
    role: Mapped[str | None] = mapped_column(String(50))
    processing_id: Mapped[str] = mapped_column(String(36), ForeignKey("email_processing.id"), nullable=False, unique=True)
    dt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_type: Mapped[DeadlineType | None] = mapped_column(SQLAlchemyEnum(DeadlineType))
    interview_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    interview_type: Mapped[InterviewType | None] = mapped_column(SQLAlchemyEnum(InterviewType))
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime]  = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    application: Mapped["Application"] = relationship(
        back_populates="stage_events"
    )

    email_processing_record: Mapped["EmailProcessing"] = relationship(
        back_populates="stage_event"
    )


class EmailRecord(Base):
    __tablename__ = "email_record"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_message_id",
            name="uq_email_provider_message",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(63), nullable=False)
    provider_message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[str] = mapped_column(String(8), ForeignKey("user.id"), nullable=False)
    sender: Mapped[str] = mapped_column(String(320), nullable=False)
    recipient: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    raw_html: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime]  = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="email_records"
    )

    processing: Mapped["EmailProcessing"] = relationship(
        back_populates="email"
    )


class EmailProcessing(Base):
    __tablename__ = "email_processing"
    __table_args__ = (
        CheckConstraint(
            "classifier_confidence >= 0 AND classifier_confidence <= 1",
            name="ck_classifier_confidence"
        ),
        CheckConstraint(
            "extractor_confidence >= 0 AND extractor_confidence <= 1",
            name="ck_extractor_confidence"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email_id: Mapped[int] = mapped_column(Integer, ForeignKey("email_record.id"), nullable=False, unique=True)
    user_id: Mapped[str] = mapped_column(String(8), ForeignKey("user.id"), nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(
        SQLAlchemyEnum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.PENDING
    )

    is_relevant: Mapped[bool | None] = mapped_column(Boolean)
    classifier_confidence: Mapped[float | None] = mapped_column(Float)
    classifier_version: Mapped[str | None] = mapped_column(String(50))
    extractor_confidence: Mapped[float | None] = mapped_column(Float)
    extractor_version: Mapped[str | None] = mapped_column(String(50))
    extractor_evidence: Mapped[str | None] = mapped_column(Text)

    company_raw: Mapped[str | None] = mapped_column(String(255))
    role_raw: Mapped[str | None] = mapped_column(String(50))
    next_action: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime]  = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    email: Mapped["EmailRecord"] = relationship(
        back_populates="processing"
    )

    stage_event: Mapped["StageEvent | None"] = relationship(
        back_populates="email_processing_record",
        cascade="all, delete-orphan",
        uselist=False
    )

    user: Mapped["User"] = relationship(
        back_populates="email_processings"
    )

    manual_review_items: Mapped[list["ManualReviewItem"]] = relationship(
        back_populates="email"
    )


class ApplicationThread(Base):
    __tablename__ = "application_thread"

    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("application.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(255), primary_key=True)
    provider_thread_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    application: Mapped["Application"] = relationship(
        back_populates="threads"
    )


class Company(Base):
    __tablename__ = "company"

    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(2048))
    linkedin_url: Mapped[str | None] = mapped_column(String(2048))
    industry: Mapped[str | None] = mapped_column(String(100))
    size: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime]  = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="company"
    )

    aliases: Mapped[list["CompanyAlias"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan"
    )


class CompanyAlias(Base):
    __tablename__ = "company_alias"

    company_id: Mapped[str] = mapped_column(String(8), ForeignKey("company.id"), primary_key=True)
    alias: Mapped[str] = mapped_column(String(255), primary_key=True)

    company: Mapped["Company"] = relationship(
        back_populates="aliases"
    )


class ManualReviewItem(Base):
    __tablename__ = "manual_review_item"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_id = mapped_column(String(36), ForeignKey("email_processing.id"))
    reason = mapped_column(Text)
    candidate_application_ids = mapped_column(JSON)  # For a review UI to show options
    resolved = mapped_column(Boolean, default=False)
    created_at = mapped_column(DateTime, default=datetime.now(timezone.utc))

    email: Mapped["EmailProcessing"] = relationship(
        back_populates="manual_review_items"
    )