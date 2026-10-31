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
cd backend && uv run ruff check && uv run ruff format --check && uv run mypy app tests && uv run pytest
```

The backend tests need Postgres: `docker compose -f infra/compose.yml up -d postgres`.

## Database

Migrations live in `backend/migrations/` and run as the owner role `loan_desk` (the `migrate`
service does this on `docker compose up`). The API and worker connect as `loan_desk_app`, which
can't change or delete audit events. To add a migration:

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
