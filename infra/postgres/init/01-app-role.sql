-- Creates the role the API and worker log in as, with a local-only password.
-- Postgres runs this when it creates a fresh data volume; the database tests run it too.
-- In production, create this role by hand with a strong password (see README).
-- Table grants live in the Alembic migrations, not here.
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'loan_desk_app') THEN
    CREATE ROLE loan_desk_app LOGIN PASSWORD 'loan_desk_app'
      NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
END
$$;
