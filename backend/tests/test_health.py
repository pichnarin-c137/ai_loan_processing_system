import threading

import pytest
from fastapi.testclient import TestClient

from app.api import health
from app.main import app

client = TestClient(app)


def set_checks(
    monkeypatch: pytest.MonkeyPatch, *, database: bool, redis: bool, storage: bool
) -> None:
    monkeypatch.setattr(health, "check_database", lambda: database)
    monkeypatch.setattr(health, "check_redis", lambda: redis)
    monkeypatch.setattr(health, "check_storage", lambda: storage)


def test_all_checks_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    set_checks(monkeypatch, database=True, redis=True, storage=True)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": True, "redis": True, "storage": True},
    }


@pytest.mark.parametrize("failing", ["database", "redis", "storage"])
def test_any_failing_check_returns_503(monkeypatch: pytest.MonkeyPatch, failing: str) -> None:
    checks = {"database": True, "redis": True, "storage": True} | {failing: False}
    set_checks(monkeypatch, **checks)

    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"][failing] is False


def test_check_reports_false_when_service_is_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenRedis:
        def ping(self) -> bool:
            raise ConnectionError("refused")

    monkeypatch.setattr(health, "get_redis", BrokenRedis)

    assert health.check_redis() is False


def test_check_past_the_deadline_counts_as_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    release = threading.Event()

    def hanging_check() -> bool:
        release.wait()
        return True

    set_checks(monkeypatch, database=True, redis=True, storage=True)
    monkeypatch.setattr(health, "check_storage", hanging_check)
    monkeypatch.setattr(health, "CHECK_DEADLINE_SECONDS", 0.1)

    try:
        response = client.get("/api/health")
    finally:
        release.set()

    assert response.status_code == 503
    assert response.json()["checks"] == {"database": True, "redis": True, "storage": False}


def test_docs_are_served_under_api() -> None:
    assert client.get("/api/openapi.json").status_code == 200
