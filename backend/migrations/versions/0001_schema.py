"""Create the initial schema: 12 tables with constraints and indexes."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "applicants",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("full_name_km", sa.Text(), nullable=True),
        sa.Column("full_name_en", sa.Text(), nullable=True),
        sa.Column("dob", sa.Date(), nullable=False),
        sa.Column("national_id", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "full_name_km IS NOT NULL OR full_name_en IS NOT NULL",
            name=op.f("ck_applicants_has_name"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applicants")),
    )
    op.create_index(op.f("ix_applicants_national_id"), "applicants", ["national_id"], unique=False)
    op.create_index(op.f("ix_applicants_user_id"), "applicants", ["user_id"], unique=False)
    op.create_table(
        "policy_versions",
        sa.Column("version", sa.String(length=16), nullable=False),
        sa.Column("approved_by", sa.Text(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("version", name=op.f("pk_policy_versions")),
    )
    op.create_table(
        "loan_applications",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("applicant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "product",
            sa.Enum(
                "personal",
                "small_business",
                name="product",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("amount_usd", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("term_months", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column(
            "stage",
            sa.Enum(
                "DRAFT",
                "SUBMITTED",
                "EXTRACTING",
                "CHECKING",
                "ANALYST_REVIEW",
                "RISK_REVIEW",
                "MANAGER_APPROVAL",
                "INFO_REQUESTED",
                "APPROVED",
                "REJECTED",
                name="stage",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="DRAFT",
            nullable=False,
        ),
        sa.Column("policy_version", sa.String(length=16), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount_usd > 0", name=op.f("ck_loan_applications_amount_positive")),
        sa.CheckConstraint("term_months > 0", name=op.f("ck_loan_applications_term_positive")),
        sa.ForeignKeyConstraint(
            ["applicant_id"],
            ["applicants.id"],
            name=op.f("fk_loan_applications_applicant_id_applicants"),
        ),
        sa.ForeignKeyConstraint(
            ["policy_version"],
            ["policy_versions.version"],
            name=op.f("fk_loan_applications_policy_version_policy_versions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_loan_applications")),
    )
    op.create_index(
        op.f("ix_loan_applications_applicant_id"),
        "loan_applications",
        ["applicant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_loan_applications_policy_version"),
        "loan_applications",
        ["policy_version"],
        unique=False,
    )
    op.create_index(
        op.f("ix_loan_applications_stage"), "loan_applications", ["stage"], unique=False
    )
    op.create_table(
        "policy_rules",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("policy_version", sa.String(length=16), nullable=False),
        sa.Column("rule_code", sa.String(length=16), nullable=False),
        sa.Column("condition", sa.Text(), nullable=False),
        sa.Column("threshold", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column(
            "action",
            sa.Enum(
                "reject",
                "analyst_review",
                "request_info",
                "risk_review",
                "officer_verify",
                name="action",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["policy_version"],
            ["policy_versions.version"],
            name=op.f("fk_policy_rules_policy_version_policy_versions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policy_rules")),
        sa.UniqueConstraint(
            "policy_version", "rule_code", name=op.f("uq_policy_rules_policy_version_rule_code")
        ),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column(
            "actor_type",
            sa.Enum(
                "ai",
                "rule",
                "human",
                "system",
                name="actor_type",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["loan_applications.id"],
            name=op.f("fk_audit_events_application_id_loan_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index(
        op.f("ix_audit_events_application_id"), "audit_events", ["application_id"], unique=False
    )
    op.create_table(
        "decisions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column(
            "stage",
            sa.Enum(
                "DRAFT",
                "SUBMITTED",
                "EXTRACTING",
                "CHECKING",
                "ANALYST_REVIEW",
                "RISK_REVIEW",
                "MANAGER_APPROVAL",
                "INFO_REQUESTED",
                "APPROVED",
                "REJECTED",
                name="stage",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum(
                "customer",
                "officer",
                "analyst",
                "risk",
                "manager",
                "committee",
                "admin",
                name="role",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("decided_by", sa.Text(), nullable=False),
        sa.Column(
            "decision",
            sa.Enum(
                "approve",
                "reject",
                "request_info",
                name="decision",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("reason_code", sa.String(length=32), nullable=True),
        sa.Column("rule_codes", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("policy_version", sa.String(length=16), nullable=False),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.CheckConstraint(r"note ~ '\S'", name=op.f("ck_decisions_note_not_blank")),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["loan_applications.id"],
            name=op.f("fk_decisions_application_id_loan_applications"),
        ),
        sa.ForeignKeyConstraint(
            ["policy_version"],
            ["policy_versions.version"],
            name=op.f("fk_decisions_policy_version_policy_versions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decisions")),
    )
    op.create_index(
        op.f("ix_decisions_application_id"), "decisions", ["application_id"], unique=False
    )
    op.create_index(
        op.f("ix_decisions_policy_version"), "decisions", ["policy_version"], unique=False
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column(
            "doc_type",
            sa.Enum(
                "national_id",
                "payslip",
                "bank_statement",
                "business_license",
                "other",
                name="doc_type",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("uploaded_by", sa.Text(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["loan_applications.id"],
            name=op.f("fk_documents_application_id_loan_applications"),
        ),
        sa.CheckConstraint("page_count > 0", name=op.f("ck_documents_page_count_positive")),
        sa.CheckConstraint("size_bytes > 0", name=op.f("ck_documents_size_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_documents_storage_key")),
    )
    op.create_index(
        op.f("ix_documents_application_id"), "documents", ["application_id"], unique=False
    )
    op.create_index(op.f("ix_documents_sha256"), "documents", ["sha256"], unique=False)
    op.create_table(
        "risk_flags",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("flag_code", sa.String(length=32), nullable=False),
        sa.Column(
            "severity",
            sa.Enum(
                "low",
                "medium",
                "high",
                name="severity",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("source_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "cleared",
                "confirmed",
                name="status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="open",
            nullable=False,
        ),
        sa.Column("reviewed_by", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["loan_applications.id"],
            name=op.f("fk_risk_flags_application_id_loan_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_risk_flags")),
    )
    op.create_index(
        op.f("ix_risk_flags_application_id"), "risk_flags", ["application_id"], unique=False
    )
    op.create_table(
        "rule_results",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("rule_code", sa.String(length=16), nullable=False),
        sa.Column("policy_version", sa.String(length=16), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("value", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("threshold", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column(
            "action",
            sa.Enum(
                "reject",
                "analyst_review",
                "request_info",
                "risk_review",
                "officer_verify",
                name="action",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["loan_applications.id"],
            name=op.f("fk_rule_results_application_id_loan_applications"),
        ),
        sa.ForeignKeyConstraint(
            ["policy_version", "rule_code"],
            ["policy_rules.policy_version", "policy_rules.rule_code"],
            name=op.f("fk_rule_results_policy_version_policy_rules"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rule_results")),
    )
    op.create_index(
        op.f("ix_rule_results_application_id"), "rule_results", ["application_id"], unique=False
    )
    op.create_index(
        op.f("ix_rule_results_policy_version"), "rule_results", ["policy_version"], unique=False
    )
    op.create_table(
        "ai_calls",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("output_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cache_read_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cache_write_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "cost_usd", sa.Numeric(precision=12, scale=6), server_default="0", nullable=False
        ),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "succeeded",
                "failed",
                name="status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["loan_applications.id"],
            name=op.f("fk_ai_calls_application_id_loan_applications"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], name=op.f("fk_ai_calls_document_id_documents")
        ),
        sa.CheckConstraint(
            "input_tokens >= 0 AND output_tokens >= 0"
            " AND cache_read_tokens >= 0 AND cache_write_tokens >= 0",
            name=op.f("ck_ai_calls_tokens_not_negative"),
        ),
        sa.CheckConstraint("cost_usd >= 0", name=op.f("ck_ai_calls_cost_not_negative")),
        sa.CheckConstraint("latency_ms >= 0", name=op.f("ck_ai_calls_latency_not_negative")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_calls")),
    )
    op.create_index(
        op.f("ix_ai_calls_application_id"), "ai_calls", ["application_id"], unique=False
    )
    op.create_index(op.f("ix_ai_calls_document_id"), "ai_calls", ["document_id"], unique=False)
    op.create_table(
        "credit_memos",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "recommendation",
            sa.Enum(
                "approve",
                "reject",
                "refer",
                name="recommendation",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("ai_call_id", sa.Uuid(), nullable=True),
        sa.Column("citation_check_passed", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1", name=op.f("ck_credit_memos_confidence_range")
        ),
        sa.CheckConstraint("version > 0", name=op.f("ck_credit_memos_version_positive")),
        sa.ForeignKeyConstraint(
            ["ai_call_id"], ["ai_calls.id"], name=op.f("fk_credit_memos_ai_call_id_ai_calls")
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["loan_applications.id"],
            name=op.f("fk_credit_memos_application_id_loan_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_credit_memos")),
        sa.UniqueConstraint(
            "application_id", "version", name=op.f("uq_credit_memos_application_id_version")
        ),
    )
    op.create_index(
        op.f("ix_credit_memos_ai_call_id"), "credit_memos", ["ai_call_id"], unique=False
    )
    op.create_table(
        "extractions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("ai_call_id", sa.Uuid(), nullable=True),
        sa.Column("fields_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1", name=op.f("ck_extractions_confidence_range")
        ),
        sa.ForeignKeyConstraint(
            ["ai_call_id"], ["ai_calls.id"], name=op.f("fk_extractions_ai_call_id_ai_calls")
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], name=op.f("fk_extractions_document_id_documents")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extractions")),
    )
    op.create_index(op.f("ix_extractions_ai_call_id"), "extractions", ["ai_call_id"], unique=False)
    op.create_index(
        op.f("ix_extractions_document_id"), "extractions", ["document_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_extractions_document_id"), table_name="extractions")
    op.drop_index(op.f("ix_extractions_ai_call_id"), table_name="extractions")
    op.drop_table("extractions")
    op.drop_index(op.f("ix_credit_memos_ai_call_id"), table_name="credit_memos")
    op.drop_table("credit_memos")
    op.drop_index(op.f("ix_ai_calls_document_id"), table_name="ai_calls")
    op.drop_index(op.f("ix_ai_calls_application_id"), table_name="ai_calls")
    op.drop_table("ai_calls")
    op.drop_index(op.f("ix_rule_results_policy_version"), table_name="rule_results")
    op.drop_index(op.f("ix_rule_results_application_id"), table_name="rule_results")
    op.drop_table("rule_results")
    op.drop_index(op.f("ix_risk_flags_application_id"), table_name="risk_flags")
    op.drop_table("risk_flags")
    op.drop_index(op.f("ix_documents_sha256"), table_name="documents")
    op.drop_index(op.f("ix_documents_application_id"), table_name="documents")
    op.drop_table("documents")
    op.drop_index(op.f("ix_decisions_policy_version"), table_name="decisions")
    op.drop_index(op.f("ix_decisions_application_id"), table_name="decisions")
    op.drop_table("decisions")
    op.drop_index(op.f("ix_audit_events_application_id"), table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_table("policy_rules")
    op.drop_index(op.f("ix_loan_applications_stage"), table_name="loan_applications")
    op.drop_index(op.f("ix_loan_applications_policy_version"), table_name="loan_applications")
    op.drop_index(op.f("ix_loan_applications_applicant_id"), table_name="loan_applications")
    op.drop_table("loan_applications")
    op.drop_table("policy_versions")
    op.drop_index(op.f("ix_applicants_user_id"), table_name="applicants")
    op.drop_index(op.f("ix_applicants_national_id"), table_name="applicants")
    op.drop_table("applicants")
