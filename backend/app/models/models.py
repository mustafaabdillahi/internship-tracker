from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Boolean, DateTime, Enum as SQLAlchemyEnum, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class ApplicationStage(str, Enum):
    APPLIED = "applied"
    OA = "oa"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    firstname: Mapped[str | None] = mapped_column(String(30))
    surname: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)

    # TODO: Encrypt before production
    google_refresh_token: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="user"
    )


class Application(Base):
    __tablename__ = "application"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(8), ForeignKey("user.id"), nullable=False)
    company_id: Mapped[str | None] = mapped_column(String(8), ForeignKey("company.id"))
    role: Mapped[str | None] = mapped_column(String(50))
    stage: Mapped[ApplicationStage | None] = mapped_column(SQLAlchemyEnum(ApplicationStage))
    date_applied: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    loc: Mapped[str | None] = mapped_column(String(255))
    employment_type: Mapped[str | None] = mapped_column(String(50)) # e.g. Full Time, Part Time, Internship
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
    )

    email_records: Mapped[list["EmailRecord"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
    )


class StageEvent(Base):
    __tablename__ = "stage_event"

    id: Mapped[str] = mapped_column(String(12), primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("application.id"), nullable=False)
    stage: Mapped[ApplicationStage] = mapped_column(SQLAlchemyEnum(ApplicationStage))
    role: Mapped[str | None] = mapped_column(String(50))
    dt: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    application: Mapped["Application"] = relationship(
        back_populates="stage_events"
    )


class EmailRecord(Base):
    __tablename__ = "email_record"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("application.id"))
    sender: Mapped[str] = mapped_column(String(320), nullable=False)
    recipient: Mapped[str] = mapped_column(String(320), nullable=False, default=False)
    subject: Mapped[str | None] = mapped_column(String(500))
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    raw_text: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    raw_html: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime]  = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    application: Mapped["Application | None"] = relationship(
        back_populates="email_records"
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
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="company"
    )