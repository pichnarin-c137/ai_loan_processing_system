import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDPK, Base, CreatedAt, str_enum
from app.models.enums import DocType, Product, Stage

# User references (user_id, created_by, uploaded_by, ...) are plain Text with no FK:
# Better Auth owns the user table (Step 4).


class Applicant(Base):
    __tablename__ = "applicants"
    __table_args__ = (
        CheckConstraint("full_name_km IS NOT NULL OR full_name_en IS NOT NULL", name="has_name"),
    )

    id: Mapped[UUIDPK]
    user_id: Mapped[str | None] = mapped_column(Text, index=True)  # null for walk-ins
    full_name_km: Mapped[str | None] = mapped_column(Text)
    full_name_en: Mapped[str | None] = mapped_column(Text)
    dob: Mapped[date]
    national_id: Mapped[str] = mapped_column(Text, index=True)
    phone: Mapped[str] = mapped_column(Text)
    created_at: Mapped[CreatedAt]


class LoanApplication(Base):
    __tablename__ = "loan_applications"
    __table_args__ = (
        CheckConstraint("amount_usd > 0", name="amount_positive"),
        CheckConstraint("term_months > 0", name="term_positive"),
    )

    id: Mapped[UUIDPK]
    applicant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applicants.id"), index=True)
    product: Mapped[Product] = mapped_column(str_enum(Product, "product"))
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    term_months: Mapped[int] = mapped_column(Integer)
    purpose: Mapped[str] = mapped_column(Text)
    stage: Mapped[Stage] = mapped_column(
        str_enum(Stage, "stage"), server_default=Stage.DRAFT.value, index=True
    )
    # Set at submit.
    policy_version: Mapped[str | None] = mapped_column(
        String(16), ForeignKey("policy_versions.version"), index=True
    )
    created_by: Mapped[str] = mapped_column(Text)
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    submitted_at: Mapped[datetime | None]


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUIDPK]
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loan_applications.id"), index=True
    )
    doc_type: Mapped[DocType] = mapped_column(str_enum(DocType, "doc_type"))
    storage_key: Mapped[str] = mapped_column(Text, unique=True)  # S3 object key
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    page_count: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    uploaded_by: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())
