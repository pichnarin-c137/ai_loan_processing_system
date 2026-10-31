import uuid
from collections.abc import Mapping
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent
from app.models.enums import ActorType


def record(
    session: Session,
    *,
    actor_type: ActorType,
    actor_id: str | None,
    action: str,
    payload: Mapping[str, Any] | None = None,
    application_id: uuid.UUID | None = None,
) -> AuditEvent:
    """Add an audit event to the session.

    The event joins the caller's transaction, so it commits or rolls back with the
    change it describes. Flush the parent row first if you pass its server-generated id.
    """
    event = AuditEvent(
        application_id=application_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        payload_json=jsonable_encoder(dict(payload or {})),
    )
    session.add(event)
    return event
