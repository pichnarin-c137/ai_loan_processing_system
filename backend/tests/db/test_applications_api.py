import io
import json
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from botocore.exceptions import EndpointConnectionError
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfWriter
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, current_user
from app.core.db import get_session
from app.core.storage import get_s3_client
from app.main import create_app
from app.models.enums import Role


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fail = False

    def put_object(self, *, Bucket: str, Key: str, Body: Any, **_kwargs: Any) -> None:  # noqa: N803
        if self.fail:
            raise EndpointConnectionError(endpoint_url="http://s3.invalid")
        self.objects[Key] = Body.read()


class Harness:
    def __init__(self, client: TestClient, s3: FakeS3, engine: Engine) -> None:
        self.client = client
        self.s3 = s3
        self.engine = engine
        self.user = CurrentUser(id=f"user-a-{uuid.uuid4()}", role=Role.CUSTOMER)
        self.other = CurrentUser(id=f"user-b-{uuid.uuid4()}", role=Role.CUSTOMER)
        self.current = self.user

    def as_user(self, user: CurrentUser) -> None:
        self.current = user

    def query(self, sql: str, **params: Any) -> list[Any]:
        with Session(self.engine) as session:
            return list(session.execute(text(sql), params))


@pytest.fixture
def h(app_engine: Engine) -> Iterator[Harness]:
    app = create_app()
    s3 = FakeS3()
    harness = Harness(TestClient(app), s3, app_engine)

    def override_session() -> Iterator[Session]:
        with Session(app_engine) as session:
            yield session

    app.dependency_overrides[current_user] = lambda: harness.current
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_s3_client] = lambda: s3
    yield harness
    app.dependency_overrides.clear()


LOAN: dict[str, Any] = {
    "product": "personal",
    "currency": "USD",
    "amount": "1500.50",
    "term_months": 12,
    "purpose": "Buy a motorbike",
}
APPLICANT: dict[str, Any] = {
    "full_name_km": "",
    "full_name_en": " Sok Dara ",
    "dob": "1990-05-01",
    "national_id": "123456789",
    "phone": "012 345-678",
}


def pdf(pages: int = 1) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=100, height=100)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def png() -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (10, 10)).save(out, format="PNG")
    return out.getvalue()


def create(h: Harness, **overrides: Any) -> dict[str, Any]:
    response = h.client.post("/api/applications", json={**LOAN, **overrides})
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def upload(h: Harness, app_id: str, doc_type: str, data: bytes | None = None) -> Any:
    return h.client.put(
        f"/api/applications/{app_id}/documents/{doc_type}",
        content=data if data is not None else pdf(),
        headers={"content-type": "application/pdf"},
    )


def complete(h: Harness) -> str:
    app_id: str = create(h)["id"]
    assert h.client.put(f"/api/applications/{app_id}/applicant", json=APPLICANT).status_code == 200
    for doc_type in ("national_id", "payslip", "bank_statement"):
        assert upload(h, app_id, doc_type).status_code == 201
    return app_id


def types(response: Any) -> list[str]:
    return [error["type"] for error in response.json()["detail"]]


def test_create_read_and_list(h: Harness) -> None:
    usd = create(h)
    khr = create(h, currency="KHR", amount="4000000", product="small_business")
    assert usd["status"] == "draft"
    assert usd["applicant"] is None
    assert usd["missing"] == ["applicant", "national_id", "payslip", "bank_statement"]
    assert khr["required_documents"][-1] == "business_license"
    got = h.client.get(f"/api/applications/{usd['id']}").json()
    assert got["amount"] == "1500.50"
    ids = [a["id"] for a in h.client.get("/api/applications").json()]
    assert ids == [khr["id"], usd["id"]]


def test_update_loan(h: Harness) -> None:
    app_id = create(h)["id"]
    response = h.client.put(
        f"/api/applications/{app_id}/loan", json={**LOAN, "term_months": 24, "purpose": "Other"}
    )
    assert response.status_code == 200
    assert response.json()["term_months"] == 24
    rows = h.query(
        "SELECT payload_json FROM audit_events WHERE application_id = :i "
        "AND action = 'application.updated'",
        i=app_id,
    )
    assert rows[0][0] == {"fields": ["term_months", "purpose"]}


def test_switching_product_removes_unneeded_documents(h: Harness) -> None:
    app_id = create(h, product="small_business")["id"]
    first = upload(h, app_id, "business_license").json()["id"]
    response = h.client.put(f"/api/applications/{app_id}/loan", json=LOAN)
    assert response.status_code == 200
    assert "business_license" not in [d["doc_type"] for d in response.json()["documents"]]
    rows = h.query(
        "SELECT payload_json FROM audit_events WHERE application_id = :i "
        "AND action = 'application.updated'",
        i=app_id,
    )
    assert rows[0][0] == {"fields": ["product"], "removed_document_ids": [first]}


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"amount": "10.123"}, "amount_decimals"),
        ({"currency": "KHR", "amount": "1000.5"}, "amount_whole_riel"),
        ({"amount": "20000.01"}, "amount_too_high"),
        ({"amount": "1e30"}, "amount_too_high"),
        ({"currency": "KHR", "amount": "80000001"}, "amount_too_high"),
        ({"term_months": 2}, "greater_than_equal"),
        ({"term_months": 61}, "less_than_equal"),
        ({"purpose": "  "}, "string_too_short"),
        ({"purpose": "x" * 501}, "string_too_long"),
    ],
)
def test_loan_validation(h: Harness, overrides: dict[str, Any], code: str) -> None:
    response = h.client.post("/api/applications", json={**LOAN, **overrides})
    assert response.status_code == 422
    assert types(response) == [code]


def test_khr_at_the_limit_is_ok(h: Harness) -> None:
    create(h, currency="KHR", amount="80000000")


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"full_name_en": " "}, "name_required"),
        ({"dob": "2999-01-01"}, "age_range"),
        ({"dob": "1900-01-01"}, "age_range"),
        ({"national_id": "12345"}, "national_id_format"),
        ({"phone": "123"}, "phone_format"),
    ],
)
def test_applicant_validation(h: Harness, overrides: dict[str, Any], code: str) -> None:
    app_id = create(h)["id"]
    response = h.client.put(
        f"/api/applications/{app_id}/applicant", json={**APPLICANT, **overrides}
    )
    assert response.status_code == 422
    assert types(response) == [code]


def test_applicant_is_saved_normalized_and_updated(h: Harness) -> None:
    app_id = create(h)["id"]
    first = h.client.put(f"/api/applications/{app_id}/applicant", json=APPLICANT).json()
    assert first["applicant"]["phone"] == "012345678"
    assert first["applicant"]["full_name_km"] is None
    assert first["applicant"]["full_name_en"] == "Sok Dara"
    again = h.client.put(
        f"/api/applications/{app_id}/applicant", json={**APPLICANT, "phone": "+855 12 345 678"}
    ).json()
    assert again["applicant"]["phone"] == "+85512345678"
    assert h.query("SELECT count(*) FROM applicants WHERE user_id = :u", u=h.user.id)[0][0] == 1


def test_loan_options(h: Harness) -> None:
    body = h.client.get("/api/loan-options").json()
    assert body["policy_version"] == "2026.1"
    assert float(body["khr_per_usd"]) == 4000
    assert float(body["max_amount"]["USD"]) == 20000
    assert float(body["max_amount"]["KHR"]) == 80000000
    assert body["products"] == ["personal", "small_business"]


def test_other_users_get_404(h: Harness) -> None:
    app_id = complete(h)
    h.as_user(h.other)
    base = f"/api/applications/{app_id}"
    responses = [
        h.client.get(base),
        h.client.put(f"{base}/loan", json=LOAN),
        h.client.put(f"{base}/applicant", json=APPLICANT),
        upload(h, app_id, "payslip"),
        h.client.post(f"{base}/submit", json={"confirm_sample": True}),
    ]
    for response in responses:
        assert response.status_code == 404
        assert response.json()["detail"] == {"code": "not_found"}
    assert h.client.get("/api/applications").json() == []


def test_staff_get_403(h: Harness) -> None:
    h.as_user(CurrentUser(id="staff", role=Role.ANALYST))
    assert h.client.get("/api/applications").status_code == 403
    assert h.client.post("/api/applications", json=LOAN).status_code == 403


def test_upload_and_replace(h: Harness) -> None:
    app_id = create(h)["id"]
    first = upload(h, app_id, "payslip")
    assert first.status_code == 201
    assert first.json()["page_count"] == 1
    assert first.json()["content_type"] == "application/pdf"
    key = f"applications/{app_id}/documents/{first.json()['id']}"
    assert key in h.s3.objects
    second = upload(h, app_id, "payslip", pdf(2))
    assert second.json()["page_count"] == 2
    detail = h.client.get(f"/api/applications/{app_id}").json()
    assert [d["id"] for d in detail["documents"]] == [second.json()["id"]]
    rows = h.query(
        "SELECT id::text, replaced_at IS NULL FROM documents WHERE application_id = :i",
        i=app_id,
    )
    assert {(r[0], r[1]) for r in rows} == {
        (first.json()["id"], False),
        (second.json()["id"], True),
    }


def test_upload_png(h: Harness) -> None:
    app_id = create(h)["id"]
    response = upload(h, app_id, "national_id", png())
    assert response.json()["content_type"] == "image/png"


def test_upload_unneeded_type(h: Harness) -> None:
    app_id = create(h)["id"]
    response = upload(h, app_id, "business_license")
    assert response.status_code == 422
    assert response.json()["detail"] == {"code": "doc_type_not_needed"}


def test_upload_storage_failure(h: Harness) -> None:
    app_id = create(h)["id"]
    h.s3.fail = True
    response = upload(h, app_id, "payslip")
    assert response.status_code == 503
    assert response.json()["detail"] == {"code": "storage_unavailable"}
    assert h.query("SELECT count(*) FROM documents WHERE application_id = :i", i=app_id)[0][0] == 0


def test_upload_too_large(h: Harness) -> None:
    app_id = create(h)["id"]
    response = upload(h, app_id, "payslip", b"%PDF-" + b"0" * (11 * 1024 * 1024))
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "file_too_large"


def test_submit_incomplete(h: Harness) -> None:
    app_id = create(h)["id"]
    response = h.client.post(f"/api/applications/{app_id}/submit", json={"confirm_sample": True})
    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "incomplete",
        "missing": ["applicant", "national_id", "payslip", "bank_statement"],
    }


def test_submit_flow(h: Harness) -> None:
    app_id = complete(h)
    url = f"/api/applications/{app_id}/submit"
    assert h.client.post(url, json={"confirm_sample": False}).status_code == 422
    response = h.client.post(url, json={"confirm_sample": True})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "checking"
    assert body["submitted_at"] is not None
    assert body["missing"] == []
    row = h.query("SELECT stage, policy_version FROM loan_applications WHERE id = :i", i=app_id)[0]
    assert tuple(row) == ("SUBMITTED", "2026.1")

    assert h.client.post(url, json={"confirm_sample": True}).status_code == 409
    after = h.client.put(f"/api/applications/{app_id}/loan", json=LOAN)
    assert (after.status_code, after.json()["detail"]) == (409, {"code": "not_draft"})
    assert upload(h, app_id, "payslip").json()["detail"] == {"code": "not_draft"}


def test_responses_hide_internal_fields(h: Harness) -> None:
    app_id = complete(h)
    texts = [
        h.client.get(f"/api/applications/{app_id}").text,
        h.client.get("/api/applications").text,
        upload(h, app_id, "payslip").text,
    ]
    for body in texts:
        for key in ("stage", "storage_key", "sha256"):
            assert f'"{key}"' not in body


def test_audit_trail_has_no_personal_values(h: Harness) -> None:
    app_id = complete(h)
    h.client.put(f"/api/applications/{app_id}/loan", json={**LOAN, "term_months": 6})
    h.client.post(f"/api/applications/{app_id}/submit", json={"confirm_sample": True})
    rows = h.query(
        "SELECT action, payload_json FROM audit_events WHERE application_id = :i", i=app_id
    )
    actions = {row[0] for row in rows}
    assert actions == {
        "application.created",
        "application.updated",
        "applicant.saved",
        "document.uploaded",
        "application.submitted",
    }
    dump = json.dumps([row[1] for row in rows])
    for secret in ("123456789", "012345678", "Sok Dara", "1990-05-01", "Buy a motorbike"):
        assert secret not in dump
