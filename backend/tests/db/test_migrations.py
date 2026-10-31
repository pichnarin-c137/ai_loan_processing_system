from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text


def test_models_match_migrations(owner_engine: Engine, alembic_config: Config) -> None:
    with owner_engine.connect() as conn:
        alembic_config.attributes["connection"] = conn
        command.check(alembic_config)


def test_policy_2026_1_has_six_rules(owner_engine: Engine) -> None:
    with owner_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT rule_code FROM policy_rules WHERE policy_version = '2026.1'")
        )
        codes = {row[0] for row in rows}
    assert codes == {"DTI-01", "INC-02", "AMT-03", "DOC-04", "KYC-05", "EXT-06"}


def test_key_check_constraints_exist(owner_engine: Engine) -> None:
    with owner_engine.connect() as conn:
        rows = conn.execute(text("SELECT conname FROM pg_constraint WHERE contype = 'c'"))
        names = {row[0] for row in rows}
    assert {
        "ck_loan_applications_stage",
        "ck_loan_applications_amount_positive",
        "ck_decisions_note_not_blank",
    } <= names
