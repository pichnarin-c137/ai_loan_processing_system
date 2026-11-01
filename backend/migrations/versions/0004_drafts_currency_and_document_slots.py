"""Drafts, currency, replaceable documents and the KHR rate."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("loan_applications", "amount_usd", new_column_name="amount")
    op.alter_column(
        "loan_applications",
        "amount",
        existing_type=sa.Numeric(12, 2),
        type_=sa.Numeric(14, 2),
        existing_nullable=False,
    )
    op.add_column(
        "loan_applications",
        sa.Column("currency", sa.String(length=32), nullable=False, server_default="USD"),
    )
    op.alter_column("loan_applications", "currency", server_default=None)
    op.create_check_constraint(
        op.f("ck_loan_applications_currency"), "loan_applications", "currency IN ('USD', 'KHR')"
    )
    op.drop_constraint(
        op.f("ck_loan_applications_amount_positive"), "loan_applications", type_="check"
    )
    op.create_check_constraint(
        op.f("ck_loan_applications_amount_positive"), "loan_applications", "amount > 0"
    )
    op.alter_column("loan_applications", "applicant_id", existing_type=sa.Uuid(), nullable=True)
    op.create_check_constraint(
        op.f("ck_loan_applications_applicant_after_draft"),
        "loan_applications",
        "stage = 'DRAFT' OR applicant_id IS NOT NULL",
    )

    op.add_column("documents", sa.Column("replaced_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "uq_documents_active_doc_type",
        "documents",
        ["application_id", "doc_type"],
        unique=True,
        postgresql_where=sa.text("replaced_at IS NULL"),
    )

    op.add_column(
        "policy_versions",
        sa.Column("khr_per_usd", sa.Numeric(10, 2), nullable=False, server_default=sa.text("4000")),
    )
    op.execute("UPDATE policy_versions SET khr_per_usd = 4000 WHERE version = '2026.1'")
    op.alter_column("policy_versions", "khr_per_usd", server_default=None)
    op.create_check_constraint(
        op.f("ck_policy_versions_khr_per_usd_positive"), "policy_versions", "khr_per_usd > 0"
    )


def downgrade() -> None:
    riel = op.get_bind().execute(
        sa.text("SELECT 1 FROM loan_applications WHERE currency = 'KHR' LIMIT 1")
    )
    if riel.first() is not None:
        raise RuntimeError("Cannot downgrade: riel applications would become dollar amounts")
    op.drop_constraint(
        op.f("ck_policy_versions_khr_per_usd_positive"), "policy_versions", type_="check"
    )
    op.drop_column("policy_versions", "khr_per_usd")

    op.drop_index("uq_documents_active_doc_type", table_name="documents")
    op.drop_column("documents", "replaced_at")

    op.drop_constraint(
        op.f("ck_loan_applications_applicant_after_draft"), "loan_applications", type_="check"
    )
    # Fails if drafts exist: they have no applicant and the old schema cannot hold them.
    op.alter_column("loan_applications", "applicant_id", existing_type=sa.Uuid(), nullable=False)
    op.drop_constraint(
        op.f("ck_loan_applications_amount_positive"), "loan_applications", type_="check"
    )
    op.drop_constraint(op.f("ck_loan_applications_currency"), "loan_applications", type_="check")
    op.drop_column("loan_applications", "currency")
    op.alter_column(
        "loan_applications",
        "amount",
        existing_type=sa.Numeric(14, 2),
        type_=sa.Numeric(12, 2),
        existing_nullable=False,
    )
    op.alter_column("loan_applications", "amount", new_column_name="amount_usd")
    op.create_check_constraint(
        op.f("ck_loan_applications_amount_positive"), "loan_applications", "amount_usd > 0"
    )
