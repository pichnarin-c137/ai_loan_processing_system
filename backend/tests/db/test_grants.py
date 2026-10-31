import pytest
from sqlalchemy import Engine, text

from app.models import Base

APP_ROLE = "loan_desk_app"
PRIVILEGES = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"]
CRUD = {"SELECT", "INSERT", "UPDATE", "DELETE"}

EXPECTED: dict[str, set[str]] = {
    "applicants": CRUD,
    "loan_applications": CRUD,
    "documents": CRUD,
    "ai_calls": CRUD,
    "extractions": CRUD,
    "credit_memos": CRUD,
    "rule_results": CRUD,
    "risk_flags": CRUD,
    "audit_events": {"SELECT", "INSERT"},
    "decisions": {"SELECT", "INSERT"},
    "policy_versions": {"SELECT"},
    "policy_rules": {"SELECT"},
}


def has_privilege(engine: Engine, table: str, privilege: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT has_table_privilege(:role, :t, :p)"),
            {"role": APP_ROLE, "t": table, "p": privilege},
        )
        return bool(result.scalar())


def test_every_table_has_an_expected_grant_entry() -> None:
    assert set(EXPECTED) == set(Base.metadata.tables), (
        "A table was added or removed: update EXPECTED and add a GRANT in a migration"
    )


@pytest.mark.parametrize("table", sorted(EXPECTED))
def test_app_role_table_privileges(owner_engine: Engine, table: str) -> None:
    for privilege in PRIVILEGES:
        assert has_privilege(owner_engine, table, privilege) == (privilege in EXPECTED[table]), (
            f"{privilege} on {table}"
        )


@pytest.mark.parametrize("privilege", PRIVILEGES)
def test_app_role_has_nothing_on_alembic_version(owner_engine: Engine, privilege: str) -> None:
    assert not has_privilege(owner_engine, "alembic_version", privilege)


def test_app_role_cannot_create_in_public_schema(owner_engine: Engine) -> None:
    with owner_engine.connect() as conn:
        result = conn.execute(
            text("SELECT has_schema_privilege(:role, 'public', 'CREATE')"), {"role": APP_ROLE}
        )
        assert result.scalar() is False
