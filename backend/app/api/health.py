import logging
from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import get_engine
from app.core.redis_client import get_redis
from app.core.storage import get_s3_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthChecks(BaseModel):
    database: bool
    redis: bool
    storage: bool


class HealthReport(BaseModel):
    status: Literal["ok", "degraded"]
    checks: HealthChecks


# Each check logs the error and returns False; the response itself never includes error details.


def check_database() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("database health check failed")
        return False
    return True


def check_redis() -> bool:
    try:
        get_redis().ping()
    except Exception:
        logger.exception("redis health check failed")
        return False
    return True


def check_storage() -> bool:
    try:
        get_s3_client().head_bucket(Bucket=get_settings().s3_bucket)
    except Exception:
        logger.exception("storage health check failed")
        return False
    return True


@router.get("/health", responses={503: {"model": HealthReport, "description": "A check failed"}})
def health(response: Response) -> HealthReport:
    checks = HealthChecks(database=check_database(), redis=check_redis(), storage=check_storage())
    ok = checks.database and checks.redis and checks.storage
    if not ok:
        response.status_code = 503
    return HealthReport(status="ok" if ok else "degraded", checks=checks)
