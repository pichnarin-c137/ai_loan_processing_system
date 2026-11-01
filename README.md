# Loan Desk

AI-assisted loan processing: the AI reads documents and drafts the analysis, code runs the policy
checks, people decide. All data is fictional; the name is set by `APP_NAME`.

- `frontend/`: SvelteKit SPA
- `auth/`: Hono auth service
- `backend/`: FastAPI and Dramatiq
- `infra/`: Docker Compose

## Run it

Needs Node 26, pnpm 11.9, uv 0.13, Docker, and [safe-chain](https://github.com/AikidoSec/safe-chain).

```sh
pnpm install && (cd backend && uv sync)
export UID GID=$(id -g)   # so the web container writes files as you
docker compose -f infra/compose.yml up --build
```

Open <http://localhost:5173>. API docs: <http://localhost:8000/api/docs>. Postgres is on port
`5433`. After changing worker code, run `docker compose -f infra/compose.yml restart worker`.

The `web` container only works on Linux. On macOS or Windows, run `pnpm --filter frontend dev` on
the host instead.

## Check it

```sh
pnpm lint && pnpm typecheck && pnpm format:check && pnpm spell && pnpm test && pnpm e2e
cd backend && uv run ruff check && uv run ruff format --check && uv run mypy app tests scripts && uv run pytest
```

The backend and auth tests need Postgres: `docker compose -f infra/compose.yml up -d postgres`.
They recreate the `loan_desk_test` and `loan_desk_auth_test` databases, so they refuse to run
against anything but `localhost`.

After changing an API route or schema, run `pnpm gen:api`. It writes the OpenAPI schema to
`frontend/src/lib/api/openapi.json` and the frontend's types to `schema.d.ts`; commit both. CI fails
if either is out of date.

## Accounts

Sign-up is by invite only. Create the first admin once the stack is up:

```sh
ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD='at-least-12-chars' ADMIN_NAME=Admin \
  docker compose -f infra/compose.yml run --rm -e ADMIN_EMAIL -e ADMIN_PASSWORD -e ADMIN_NAME auth node src/seed-admin.ts
```

The admin signs in at `/login` and creates invite links with a role at `/admin/users`. There is no
email yet, so send the link yourself. The token sits after the `#`, so it never reaches server logs,
and only its hash is stored.

The auth service (Better Auth) keeps its tables in the `auth` schema and connects as
`loan_desk_auth`, which has no access to the loan tables; `loan_desk_app` has none in `auth`. The
`auth-migrate` service creates the tables on `docker compose up`. FastAPI never sees passwords: the
browser gets a 15-minute JWT from `/api/auth/token`, and the API checks it against
`/api/auth/jwks`. A banned user's token stays valid until it expires.

In production:

- Create the role and schema by hand with a strong password before the first deploy (the init
  script only runs locally), then point `AUTH_DATABASE_URL` at that role:

  ```sql
  CREATE ROLE loan_desk_auth LOGIN PASSWORD '<strong password>';
  CREATE SCHEMA auth AUTHORIZATION loan_desk_auth;
  ```

- Set `BETTER_AUTH_SECRET` (`openssl rand -base64 32`) on the auth service only. It refuses to
  start in production without one.
- Sign-in is rate limited per client IP, read from `X-Forwarded-For`. The proxy in front of the
  auth service must replace that header with the address it saw (Caddy's `reverse_proxy` does by
  default); otherwise a client can pick its own IP and dodge the limit. If a proxy adds to the
  header instead, list the proxies' IPs or CIDR ranges in `AUTH_TRUSTED_PROXIES`: the auth service
  then takes the last address that isn't one of them. Without it, a header with several addresses
  gives no IP, and all those requests share one limit. Locally they count as `127.0.0.1`, which is
  fine for the Vite dev proxy (`xfwd` adds to the header).

## Database

Migrations live in `backend/migrations/` and run as the owner role `loan_desk` (the `migrate`
service does this on `docker compose up`). Only the migration step gets `MIGRATION_DATABASE_URL`;
never put it in `.env`. The API and worker connect as `loan_desk_app`, which can only add rows to
the history tables (audit events, decisions, AI calls, rule results, credit memos). To add a
migration:

```sh
cd backend && uv run alembic revision --autogenerate -m "add widgets"
```

Review the generated file and grant `loan_desk_app` access to every new table in it; a test fails
otherwise. `infra/postgres/init/01-app-role.sql` creates `loan_desk_app` locally when the Postgres
volume is new (if yours is older, run `docker compose -f infra/compose.yml down -v` once). In
production, create that role by hand with a strong password before the first deploy.

## Packages

Install only through safe-chain. New versions must be 3+ days old, and only packages under
`allowBuilds` may run install scripts.
