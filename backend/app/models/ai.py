import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDPK, Base, CreatedAt, str_enum
from app.models.enums import AiCallStatus, Recommendation


class AiCall(Base):
    __tablename__ = "ai_calls"

    id: Mapped[UUIDPK]
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("loan_applications.id"), index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id"), index=True)
    task: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    prompt_version: Mapped[str] = mapped_column(Text)
    input_tokens: Mapped[int] = mapped_column(Integer, server_default="0")
    output_tokens: Mapped[int] = mapped_column(Integer, server_default="0")
    cache_read_tokens: Mapped[int] = mapped_column(Integer, server_default="0")
    cache_write_tokens: Mapped[int] = mapped_column(Integer, server_default="0")
    # A call costs fractions of a cent.
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), server_default="0")
    latency_ms: Mapped[int] = mapped_column(Integer)
    status: Mapped[AiCallStatus] = mapped_column(str_enum(AiCallStatus, "status"))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[CreatedAt]


class Extraction(Base):
    __tablename__ = "extractions"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    id: Mapped[UUIDPK]
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    # Null when an officer types the fields by hand.
    ai_call_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ai_calls.id"), index=True)
    fields_json: Mapped[dict[str, Any]]
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    created_at: Mapped[CreatedAt]


class CreditMemo(Base):
    __tablename__ = "credit_memos"
    __table_args__ = (
        UniqueConstraint("application_id", "version"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
    )

    id: Mapped[UUIDPK]
    # No separate index: the unique constraint leads with application_id.
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loan_applications.id"))
    version: Mapped[int] = mapped_column(Integer)
    content_json: Mapped[dict[str, Any]]
    recommendation: Mapped[Recommendation] = mapped_column(
        str_enum(Recommendation, "recommendation")
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    ai_call_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ai_calls.id"), index=True)
    citation_check_passed: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[CreatedAt]
