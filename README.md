# Loan Desk

An AI-assisted loan processing system, built as a learning project. The AI reads Khmer and English
documents and drafts the analysis; code runs the policy checks; people make every decision.

> **Sample data only.** Every person and document in this project is fictional.
> "Loan Desk" is a placeholder name, set by `APP_NAME` / `VITE_APP_NAME`.

| Part        | Stack                                                                    |
| ----------- | ------------------------------------------------------------------------ |
| `frontend/` | SvelteKit (SPA mode), Svelte 5, Tailwind CSS, Paraglide (English, Khmer) |
| `auth/`     | Hono sign-in service (Better Auth arrives in Step 4)                     |
| `backend/`  | FastAPI API and Dramatiq worker (Python 3.12, uv)                        |
| `infra/`    | Docker Compose: PostgreSQL, Redis, SeaweedFS (S3), and the apps above    |

## Setup

You need Node 26, pnpm 11.9, uv 0.13 and Docker with Compose.

1. Install [safe-chain](https://github.com/AikidoSec/safe-chain). It checks every package that
   pnpm, npm, uv and pip download, and blocks known-malicious ones:

   ```sh
   npm install --global @aikidosec/safe-chain
   safe-chain setup   # then restart your shell
   ```

2. Install dependencies. This also installs the git hooks.

   ```sh
   pnpm install
   (cd backend && uv sync)
   ```

3. Optional: `cp .env.example .env` to override settings. The local defaults work without it.

4. Start everything:

   ```sh
   docker compose -f infra/compose.yml up --build
   ```

   Open <http://localhost:5173>. The status card should show every service as OK.

| Service                        | Local address                                         |
| ------------------------------ | ----------------------------------------------------- |
| Web app (Vite, proxies `/api`) | <http://localhost:5173>                               |
| API docs                       | <http://localhost:8000/api/docs>                      |
| Auth service                   | <http://localhost:3001/api/auth/ok>                   |
| PostgreSQL                     | `localhost:5433` (user, password, db: `loan_desk`)    |
| Redis                          | `localhost:6379`                                      |
| S3 storage (SeaweedFS)         | <http://localhost:8333>, bucket `loan-desk-documents` |

The `web` container runs Vite using the `node_modules` from step 2, so it only works on Linux. On
macOS or Windows, run `docker compose -f infra/compose.yml up api worker auth` and start the
frontend on the host with `pnpm --filter frontend dev`.

## Checks

Run from the repo root. CI runs all of them on every pull request.

| Command             | What it does                                                                                   |
| ------------------- | ---------------------------------------------------------------------------------------------- |
| `pnpm lint`         | ESLint with type-aware rules                                                                   |
| `pnpm format:check` | Prettier (`pnpm format` fixes it)                                                              |
| `pnpm typecheck`    | `svelte-check` and `tsc`                                                                       |
| `pnpm spell`        | CSpell; add project words to `cspell-words.txt`                                                |
| `pnpm test`         | Vitest (frontend browser tests need `pnpm --filter frontend exec playwright install chromium`) |
| `pnpm e2e`          | Playwright against a production build                                                          |

Backend, from `backend/`: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy app tests`,
`uv run pytest`.

## Supply-chain rules

- Install packages only through safe-chain.
- New package versions must be at least 3 days old: `minimumReleaseAge` in `pnpm-workspace.yaml`,
  `exclude-newer` in `backend/pyproject.toml`.
- Packages may run install scripts only if they are listed under `allowBuilds` in
  `pnpm-workspace.yaml`.
- CI installs from the lockfiles only, and pins GitHub Actions to commit SHAs.
