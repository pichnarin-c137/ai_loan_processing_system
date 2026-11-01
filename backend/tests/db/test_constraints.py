import uuid

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Decision, Document, RuleResult
from app.models.enums import DecisionKind, DocType, Role, RuleAction, Stage
from tests.db.factories import new_application


@pytest.mark.parametrize("note", ["", "   ", "\t\r\n"])
def test_decision_note_needs_visible_text(app_engine: Engine, note: str) -> None:
    with Session(app_engine) as session:
        application = new_application(session)
        session.add(application)
        session.flush()
        session.add(
            Decision(
                application_id=application.id,
                stage=Stage.ANALYST_REVIEW,
                role=Role.ANALYST,
                decided_by="tester",
                decision=DecisionKind.APPROVE,
                note=note,
                rule_codes=[],
                policy_version="2026.1",
            )
        )
        with pytest.raises(IntegrityError, match="ck_decisions_note_not_blank"):
            session.flush()


def test_rule_result_must_name_a_rule_of_its_policy_version(app_engine: Engine) -> None:
    with Session(app_engine) as session:
        application = new_application(session)
        session.add(application)
        session.flush()
        session.add(
            RuleResult(
                application_id=application.id,
                rule_code="NOPE-99",
                policy_version="2026.1",
                passed=True,
                action=RuleAction.REJECT,
                details={},
            )
        )
        with pytest.raises(IntegrityError, match="fk_rule_results_policy_version_policy_rules"):
            session.flush()


def test_submitted_application_needs_an_applicant(app_engine: Engine) -> None:
    with Session(app_engine) as session:
        application = new_application(session)
        application.applicant_id = None
        application.stage = Stage.SUBMITTED
        session.add(application)
        with pytest.raises(IntegrityError, match="ck_loan_applications_applicant_after_draft"):
            session.flush()


def _document(application_id: object) -> Document:
    return Document(
        application_id=application_id,
        doc_type=DocType.PAYSLIP,
        storage_key=f"k-{uuid.uuid4()}",
        sha256="0" * 64,
        page_count=1,
        content_type="application/pdf",
        size_bytes=10,
        uploaded_by="tester",
    )


def test_one_active_document_per_type(app_engine: Engine) -> None:
    with Session(app_engine) as session:
        application = new_application(session)
        session.add(application)
        session.flush()
        session.add(_document(application.id))
        session.flush()
        session.add(_document(application.id))
        with pytest.raises(IntegrityError, match="uq_documents_active_doc_type"):
            session.flush()


def test_currency_must_be_known(app_engine: Engine) -> None:
    with Session(app_engine) as session:
        application = new_application(session)
        session.add(application)
        session.flush()
        with pytest.raises(IntegrityError, match="ck_loan_applications_currency"):
            session.execute(
                text("UPDATE loan_applications SET currency = 'EUR' WHERE id = :i"),
                {"i": application.id},
            )


def test_policy_2026_1_has_a_khr_rate(app_engine: Engine) -> None:
    with Session(app_engine) as session:
        rate = session.execute(
            text("SELECT khr_per_usd FROM policy_versions WHERE version = '2026.1'")
        ).scalar_one()
    assert rate == 4000
