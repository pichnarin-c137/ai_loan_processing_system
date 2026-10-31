"""Seed policy version 2026.1 and its rules."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

VERSION = "2026.1"

policy_versions = sa.table(
    "policy_versions",
    sa.column("version", sa.String),
    sa.column("approved_by", sa.Text),
    sa.column("effective_from", sa.Date),
    sa.column("notes", sa.Text),
)
policy_rules = sa.table(
    "policy_rules",
    sa.column("policy_version", sa.String),
    sa.column("rule_code", sa.String),
    sa.column("condition", sa.Text),
    sa.column("threshold", sa.Numeric),
    sa.column("action", sa.String),
)

RULES = (
    (
        "DTI-01",
        "Monthly debt payments / monthly income must not exceed the threshold",
        Decimal("0.40"),
        "reject",
    ),
    (
        "INC-02",
        "Declared income may differ from payslip income by at most the threshold (fraction)",
        Decimal("0.10"),
        "analyst_review",
    ),
    (
        "AMT-03",
        "Loan amount must not exceed the threshold x monthly income",
        Decimal("10"),
        "reject",
    ),
    (
        "DOC-04",
        "Documents must be no older than the threshold (days)",
        Decimal("90"),
        "request_info",
    ),
    (
        "KYC-05",
        "Name match score between ID and other documents (0-100, rapidfuzz) must be at "
        "least the threshold; provisional",
        Decimal("85"),
        "risk_review",
    ),
    (
        "EXT-06",
        "Every required extracted field must have confidence at least the threshold",
        Decimal("0.80"),
        "officer_verify",
    ),
)


def upgrade() -> None:
    op.bulk_insert(
        policy_versions,
        [
            {
                "version": VERSION,
                "approved_by": "seed",
                "effective_from": date(2026, 1, 1),
                "notes": "Initial policy from the project spec.",
            }
        ],
    )
    op.bulk_insert(
        policy_rules,
        [
            {
                "policy_version": VERSION,
                "rule_code": code,
                "condition": condition,
                "threshold": threshold,
                "action": action,
            }
            for code, condition, threshold, action in RULES
        ],
    )


def downgrade() -> None:
    op.execute(policy_rules.delete().where(policy_rules.c.policy_version == VERSION))
    op.execute(policy_versions.delete().where(policy_versions.c.version == VERSION))
