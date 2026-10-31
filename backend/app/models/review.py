import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDPK, Base, CreatedAt, str_enum
from app.models.enums import DecisionKind, FlagStatus, Role, RuleAction, Severity, Stage


class RuleResult(Base):
    __tablename__ = "rule_results"

    id: Mapped[UUIDPK]
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loan_applications.id"), index=True
    )
    rule_code: Mapped[str] = mapped_column(String(16))
    policy_version: Mapped[str] = mapped_column(
        String(16), ForeignKey("policy_versions.version"), index=True
    )
    passed: Mapped[bool] = mapped_column(Boolean)
    value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    threshold: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    action: Mapped[RuleAction] = mapped_column(str_enum(RuleAction, "action"))
    details: Mapped[dict[str, Any]]
    created_at: Mapped[CreatedAt]


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id: Mapped[UUIDPK]
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loan_applications.id"), index=True
    )
    flag_code: Mapped[str] = mapped_column(String(32))
    severity: Mapped[Severity] = mapped_column(str_enum(Severity, "severity"))
    explanation: Mapped[str | None] = mapped_column(Text)
    source_refs: Mapped[dict[str, Any]]
    status: Mapped[FlagStatus] = mapped_column(
        str_enum(FlagStatus, "status"), server_default=FlagStatus.OPEN.value
    )
    reviewed_by: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None]
    review_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[CreatedAt]


# Insert-only for the app: a changed decision is a new row.
class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (CheckConstraint("btrim(note) <> ''", name="note_not_blank"),)

    id: Mapped[UUIDPK]
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loan_applications.id"), index=True
    )
    stage: Mapped[Stage] = mapped_column(str_enum(Stage, "stage"))
    role: Mapped[Role] = mapped_column(str_enum(Role, "role"))
    decided_by: Mapped[str] = mapped_column(Text)
    decision: Mapped[DecisionKind] = mapped_column(str_enum(DecisionKind, "decision"))
    note: Mapped[str] = mapped_column(Text)
    reason_code: Mapped[str | None] = mapped_column(String(32))
    rule_codes: Mapped[list[str]] = mapped_column(ARRAY(Text))
    policy_version: Mapped[str] = mapped_column(
        String(16), ForeignKey("policy_versions.version"), index=True
    )
    decided_at: Mapped[datetime] = mapped_column(server_default=func.now())
