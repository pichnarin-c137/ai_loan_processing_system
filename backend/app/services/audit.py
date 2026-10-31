import json
from collections.abc import Mapping
from typing import Any

from pydantic_core import to_jsonable_python
from sqlalchemy.orm import Session

from app.models.applications import LoanApplication
from app.models.audit import AuditEvent
from app.models.enums import ActorType


def record(
    session: Session,
    *,
    actor_type: ActorType,
    actor_id: str | None,
    action: str,
    payload: Mapping[str, Any] | None = None,
    application: LoanApplication | None = None,
) -> AuditEvent:
    """Add an audit event to the session.

    The event joins the caller's transaction, so it commits or rolls back with the
    change it describes. A new application is flushed first so the event gets its id.
    Decimals in the payload are stored as strings, so amounts keep every digit.
    """
    payload_json = to_jsonable_python(dict(payload or {}))
    # Postgres JSONB rejects NaN and Infinity; fail here with a clear error instead.
    json.dumps(payload_json, allow_nan=False)

    application_id = None
    if application is not None:
        if application.id is None:
            session.add(application)
            session.flush()
        application_id = application.id

    event = AuditEvent(
        application_id=application_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        payload_json=payload_json,
    )
    session.add(event)
    return event
