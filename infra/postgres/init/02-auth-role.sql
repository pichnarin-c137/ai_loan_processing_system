-- Creates the role and schema the auth service (Better Auth) uses, with a local-only password.
-- Postgres runs this when it creates a fresh data volume; the auth tests run it too.
-- In production, create the role and schema by hand with a strong password (see README).
-- The auth role gets no grants on the loan tables, and the app role gets nothing in this schema.
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'loan_desk_auth') THEN
    CREATE ROLE loan_desk_auth LOGIN PASSWORD 'loan_desk_auth'
      NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
END
$$;

CREATE SCHEMA IF NOT EXISTS auth AUTHORIZATION loan_desk_auth;
