import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

import sqlalchemy as sa
from sqlalchemy import DateTime, MetaData, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {  # noqa: RUF012 - SQLAlchemy declarative hook
        datetime: DateTime(timezone=True),
        dict[str, Any]: JSONB,
    }


# uuidv7() is time-ordered (index-friendly) and built into Postgres 18.
UUIDPK = Annotated[uuid.UUID, mapped_column(primary_key=True, server_default=text("uuidv7()"))]
CreatedAt = Annotated[datetime, mapped_column(server_default=func.now())]


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [m.value for m in enum_cls]


def str_enum(enum_cls: type[StrEnum], name: str) -> sa.Enum:
    # Stored as text + a CHECK constraint (ck_<table>_<name>): easier to extend than a native enum.
    return sa.Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=enum_values,
        validate_strings=True,
    )
