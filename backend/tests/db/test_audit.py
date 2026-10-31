import uuid

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.models import AuditEvent
from app.models.enums import ActorType
from app.services.audit import record


def insert_event(engine: Engine) -> uuid.UUID:
    with Session(engine) as session:
        event = record(
            session,
            actor_type=ActorType.SYSTEM,
            actor_id=None,
            action=f"test.{uuid.uuid4()}",
        )
        session.commit()
        return event.id


def test_record_writes_an_event(app_engine: Engine) -> None:
    action = f"test.record.{uuid.uuid4()}"
    marker = uuid.uuid4().hex
    with Session(app_engine) as session:
        event = record(
            session,
            actor_type=ActorType.SYSTEM,
            actor_id="tester",
            action=action,
            payload={"marker": marker},
        )
        session.commit()
        event_id = event.id

    with Session(app_engine) as session:
        row = session.get(AuditEvent, event_id)
        assert row is not None
        assert row.action == action
        assert row.actor_type == ActorType.SYSTEM
        assert row.actor_id == "tester"
        assert row.application_id is None
        assert row.payload_json == {"marker": marker}
        assert row.created_at is not None


STATEMENTS = [
    pytest.param("UPDATE audit_events SET action = 'x' WHERE id = :id", id="update"),
    pytest.param("DELETE FROM audit_events WHERE id = :id", id="delete"),
    pytest.param("TRUNCATE audit_events", id="truncate"),
]


@pytest.mark.parametrize("statement", STATEMENTS)
def test_app_role_cannot_modify_audit_events(app_engine: Engine, statement: str) -> None:
    event_id = insert_event(app_engine)
    with (
        pytest.raises(DBAPIError, match="permission denied"),
        app_engine.begin() as conn,
    ):
        conn.execute(text(statement), {"id": event_id})
    with app_engine.connect() as conn:
        found = conn.execute(text("SELECT 1 FROM audit_events WHERE id = :id"), {"id": event_id})
        assert found.scalar() == 1


@pytest.mark.parametrize("statement", STATEMENTS)
def test_owner_is_blocked_by_append_only_trigger(
    owner_engine: Engine, app_engine: Engine, statement: str
) -> None:
    event_id = insert_event(app_engine)
    with (
        pytest.raises(DBAPIError, match="append-only"),
        owner_engine.begin() as conn,
    ):
        conn.execute(text(statement), {"id": event_id})
    with owner_engine.connect() as conn:
        found = conn.execute(text("SELECT 1 FROM audit_events WHERE id = :id"), {"id": event_id})
        assert found.scalar() == 1
