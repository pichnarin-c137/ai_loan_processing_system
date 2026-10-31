import uuid
from typing import Any

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDPK, Base, CreatedAt, str_enum
from app.models.enums import ActorType


# Append-only (grants + trigger in migration 0002).
class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUIDPK]
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("loan_applications.id"), index=True
    )
    actor_type: Mapped[ActorType] = mapped_column(str_enum(ActorType, "actor_type"))
    actor_id: Mapped[str | None] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]]
    created_at: Mapped[CreatedAt]
