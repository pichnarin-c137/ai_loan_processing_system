"""Grant least-privilege table access to loan_desk_app and make audit_events append-only."""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Each new table needs its own GRANT in a migration (a test checks this).
FULL_ACCESS = ("applicants", "loan_applications", "documents", "extractions", "risk_flags")
# History: a changed decision, a re-run of the rules or a new memo version adds rows.
INSERT_ONLY = ("audit_events", "decisions", "ai_calls", "rule_results", "credit_memos")
READ_ONLY = ("policy_versions", "policy_rules")
ALL_TABLES = (*FULL_ACCESS, *INSERT_ONLY, *READ_ONLY)

APP_ROLE = "loan_desk_app"


def upgrade() -> None:
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {', '.join(FULL_ACCESS)} TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON {', '.join(INSERT_ONLY)} TO {APP_ROLE}")
    op.execute(f"GRANT SELECT ON {', '.join(READ_ONLY)} TO {APP_ROLE}")

    op.execute(
        """
        CREATE FUNCTION audit_events_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'audit_events is append-only (% blocked)', TG_OP
            USING ERRCODE = 'insufficient_privilege';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_no_update_delete BEFORE UPDATE OR DELETE ON audit_events
          FOR EACH ROW EXECUTE FUNCTION audit_events_append_only()
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_no_truncate BEFORE TRUNCATE ON audit_events
          FOR EACH STATEMENT EXECUTE FUNCTION audit_events_append_only()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER audit_events_no_truncate ON audit_events")
    op.execute("DROP TRIGGER audit_events_no_update_delete ON audit_events")
    op.execute("DROP FUNCTION audit_events_append_only()")
    op.execute(f"REVOKE ALL ON {', '.join(ALL_TABLES)} FROM {APP_ROLE}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {APP_ROLE}")
