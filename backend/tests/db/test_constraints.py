import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Decision, RuleResult
from app.models.enums import DecisionKind, Role, RuleAction, Stage
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
