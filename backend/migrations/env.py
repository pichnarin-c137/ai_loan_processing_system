from typing import Any

from alembic import context
from sqlalchemy import Connection, create_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models import Base

config = context.config
target_metadata = Base.metadata


def include_name(name: str | None, type_: str, parent_names: Any) -> bool:
    # Other tools (e.g. Better Auth) own tables in this database; ignore them.
    if type_ == "table":
        return name in target_metadata.tables
    return True


def _configure_kwargs() -> dict[str, Any]:
    return {
        "target_metadata": target_metadata,
        "include_name": include_name,
        "compare_type": True,
        "compare_server_default": True,
    }


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().migration_database_url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_configure_kwargs(),
    )
    with context.begin_transaction():
        context.run_migrations()


def _run(connection: Connection) -> None:
    context.configure(connection=connection, **_configure_kwargs())
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if isinstance(connection, Connection):
        _run(connection)
        return
    engine = create_engine(get_settings().migration_database_url, poolclass=NullPool)
    with engine.connect() as conn:
        _run(conn)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
