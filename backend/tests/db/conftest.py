from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings, migration_database_url

BACKEND = Path(__file__).resolve().parents[2]
ROLE_SQL = BACKEND.parent / "infra" / "postgres" / "init" / "01-app-role.sql"
TEST_DB = "loan_desk_test"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

ADMIN_URL = make_url(migration_database_url())
OWNER_URL = ADMIN_URL.set(database=TEST_DB)
APP_URL = make_url(get_settings().database_url).set(database=TEST_DB)


def _new_config() -> Config:
    return Config(str(BACKEND / "alembic.ini"))


@pytest.fixture(scope="session")
def _test_database() -> Iterator[None]:
    # The fixture drops and recreates a database and creates a role with a known password.
    if ADMIN_URL.host not in LOCAL_HOSTS:
        pytest.fail(
            f"Database tests only run against a local Postgres, not {ADMIN_URL.host}. "
            "Check MIGRATION_DATABASE_URL.",
            pytrace=False,
        )
    admin = create_engine(
        ADMIN_URL, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 3}
    )
    try:
        with admin.connect() as conn:
            conn.exec_driver_sql(ROLE_SQL.read_text())
            conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
            conn.execute(text(f"CREATE DATABASE {TEST_DB}"))
    except OperationalError:
        admin.dispose()
        pytest.fail(
            "Database tests need Postgres at "
            f"{ADMIN_URL.render_as_string(hide_password=True)}. "
            "Start it: docker compose -f infra/compose.yml up -d postgres",
            pytrace=False,
        )

    owner = create_engine(OWNER_URL)
    try:
        cfg = _new_config()
        with owner.begin() as conn:
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")
            command.downgrade(cfg, "base")
            command.upgrade(cfg, "head")
            del cfg.attributes["connection"]
        yield
    finally:
        owner.dispose()
        with admin.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
        admin.dispose()


@pytest.fixture(scope="session")
def owner_engine(_test_database: None) -> Iterator[Engine]:
    engine = create_engine(OWNER_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def app_engine(_test_database: None) -> Iterator[Engine]:
    engine = create_engine(APP_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def alembic_config() -> Config:
    return _new_config()
