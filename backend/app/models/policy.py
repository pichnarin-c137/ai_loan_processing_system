from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDPK, Base, CreatedAt, str_enum
from app.models.enums import RuleAction


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    version: Mapped[str] = mapped_column(String(16), primary_key=True)  # e.g. "2026.1"
    approved_by: Mapped[str] = mapped_column(Text)
    effective_from: Mapped[date]
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[CreatedAt]


# Changed only through migrations; a changed rule means a new policy version.
class PolicyRule(Base):
    __tablename__ = "policy_rules"
    __table_args__ = (UniqueConstraint("policy_version", "rule_code"),)

    id: Mapped[UUIDPK]
    # No separate index: the unique constraint leads with policy_version.
    policy_version: Mapped[str] = mapped_column(String(16), ForeignKey("policy_versions.version"))
    rule_code: Mapped[str] = mapped_column(String(16))
    condition: Mapped[str] = mapped_column(Text)
    threshold: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    action: Mapped[RuleAction] = mapped_column(str_enum(RuleAction, "action"))
