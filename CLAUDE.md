# CLAUDE.md

Guidance for AI agents (and humans) working on this repository. The owner's rules
come first. Everything else here explains how to meet them to a professional standard.

## Owner's rules

1. Fix tasks as autonomously as possible. Ask only when you're unsure what's wrong or
   need a product decision.
2. Create a new branch for each item, with a short, meaningful name.
3. When an item is finished, update the shareable review page and mark the item as
   finished there (see "Tracking progress" below).
4. Whenever you learn something worth keeping (a convention, a trap, a lesson from a
   review), add it to this file.

When these rules and the rest of this file disagree, the rules win.

## Project at a glance

Seafood distribution and order management platform. Customers order seafood,
distributors fulfil orders and manage stock, and admins oversee everything.

| Layer    | Stack                                                              | Entry point                |
|----------|--------------------------------------------------------------------|----------------------------|
| Backend  | Python 3.11+, FastAPI, SQLAlchemy 2.0 (legacy `Query` style), Pydantic v2 | `backend/app/main.py`      |
| Database | PostgreSQL 16                                                      | `backend/app/models/`      |
| Auth     | JWT (python-jose, HS256) + bcrypt (passlib)                        | `backend/app/core/`        |
| Frontend | React 18, TypeScript (strict), Vite, Tailwind, Recharts, Axios     | `frontend/src/App.tsx`     |

Layout of `backend/app/`: `core/` holds config, the DB session, security and auth
dependencies; `models/` the SQLAlchemy tables; `schemas/` the Pydantic request and
response models; `routers/` one file per resource.

Roles are `ADMIN`, `DISTRIBUTOR` and `CUSTOMER`. The backend is the only place
permissions are enforced (`require_roles()` in `core/deps.py`, plus inline ownership
checks). Frontend checks only hide UI.

### Running locally

```bash
# Backend (from backend/)
python -m venv venv && venv\Scripts\activate      # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                              # point DATABASE_URL at your Postgres
python seed.py                                    # demo users and products
uvicorn app.main:app --reload                     # http://localhost:8000/docs

# Frontend (from frontend/)
npm install
npm run dev                                       # http://localhost:5173, proxies /api → :8000
```

Demo logins are in `README.md`.

### Known traps (until their backlog items are fixed)

- `docker compose up` does not work: wrong backend port and wrong proxy target (#17).
- There are no migrations. `Base.metadata.create_all()` creates missing tables but
  never alters existing ones (#18). After a model change, test against a fresh database.
- The Vite proxy target is hard-coded to `localhost:8000` (#17).
- Docker's `JWT_SECRET` isn't read by the app, which falls back to the default secret (#2).

## Backlog

`docs/backlog.md` is the source of truth for the fix items, which are numbered `#1`–`#21`.
When an item is done, its PR marks it fixed there. The shareable review page mirrors
it. See "Tracking progress" below.

## Working process

Applies to every agent session, local or cloud.

### When to stop and ask

Work autonomously. Stop only for decisions that need the owner's product judgement:

- How the business works for users: who may do what, order and stock rules,
  which statuses exist and how they change, what customers can see, and wording in the UI.
- Security trade-offs (for example, token storage or session length) and anything that
  changes how existing users log in.
- Destructive or outward-facing actions: writing to a database you didn't create,
  deploying, force-pushing, deleting branches or data, changing repository settings.
- Expanding scope beyond the item being fixed.

Everything else is yours to decide: naming, structure, refactors within scope, test
design, and choices with a conventional answer. Record each one under "Decisions I made"
in the PR, with the alternative you rejected. When you must ask, put all questions in
one message, each with your recommendation.

If you find a new problem while fixing an item, don't fix it in the same branch.
Add it to `docs/backlog.md` as a new item and mention it in the PR.

### Branches and PRs

- One backlog item per branch, created from the latest `origin/main`.
- Name: `fix/<item-number>-<2-to-4-word-summary>`, kebab-case, under ~40 characters.
  Examples: `fix/01-admin-signup`, `fix/07-stock-oversell`, `fix/08-order-status-rules`.
  Work that isn't a backlog item uses `docs/…`, `chore/…` or `feat/…`.
- Before starting, run `gh pr list`. If an open PR touches the same files, say so in your
  PR and describe how the conflict should be resolved. Merge `origin/main` into your
  branch again right before opening the PR.
- Commit in small logical steps with imperative messages
  (`Force CUSTOMER role on self-registration`).
- Never merge your own PR, never force-push, and never push to `main`. The owner merges.
- PR title: `#<n> <summary>` (for example, `#1 Stop self-registration as admin`).
- PR body sections: **Problem**, **Fix**, **Decisions I made**, **Behaviour/API changes**,
  **Interactions with open PRs**, **Testing**, **Not tested**.

### Attribution

- No `Co-authored-by`, `Claude-Session`, "Generated with Claude Code" or session links in
  commits or PR bodies.
- Check before pushing:
  `git log origin/main..HEAD --format=%B | grep -iE "co-authored-by|generated with|claude-session|claude\.ai/code"`
  must print nothing. Apply the same check to the PR description.

### Definition of done (all of these, every PR)

1. **Backend tests:** `pytest` from `backend/` passes, and the PR adds tests that fail
   without the fix and pass with it. (The test harness is being set up under #19. Until
   it exists, building it is the first step of whichever item comes first.)
2. **Frontend checks:** `npm run build` from `frontend/` (runs `tsc` and the Vite build)
   passes with no new type errors.
3. **Real API against a throwaway database,** covering success and error paths
   (wrong role → 403, bad input → 422, and so on):
   ```bash
   docker run --rm -d --name seafood-test-db -p 5433:5432 \
     -e POSTGRES_PASSWORD=test -e POSTGRES_DB=seafood_test postgres:16-alpine
   # DATABASE_URL=postgresql://postgres:test@localhost:5433/seafood_test
   # run the API on port 8010, exercise it with curl or httpx, then:
   docker stop seafood-test-db                       # --rm deletes it
   ```
   Never point tests at the development database or the Compose `pgdata` volume.
4. **Visible changes:** any change a customer, distributor or admin can see is checked
   in a browser (Playwright) for every affected role, including error and empty states.
5. **Ports:** use non-default ports (API 8010, test Postgres 5433, Vite 5183). Never stop
   a process you didn't start.
6. **Docs:** update `README.md` and this file when you change an endpoint, a command,
   an environment variable or a convention.
7. **Backlog:** mark the item fixed in `docs/backlog.md` with a one-line note.
8. **PR write-up:** the Testing section lists what ran, with results. "Not tested" says
   what wasn't tested and why.

### Code standards

**General**
- Fix the root cause, not the symptom. Keep the change scoped to the item.
- Match the surrounding code's style and comment density. Comments explain *why*, not *what*.
- No dead code, commented-out code, stray `print`/`console.log`, or unused imports.

**Python / FastAPI**
- Type hints on every function signature. Follow PEP 8. Keep the existing `db.query(...)`
  style unless the item is about changing it.
- Every endpoint declares its auth dependency (`get_current_user` or `require_roles(...)`).
  Business rules live in the backend, never only in the frontend.
- Separate input and output schemas. Never return `hashed_password` or internal-only
  fields. Validate input with Pydantic (`Field(gt=0)` and so on) rather than by hand.
- Commit once per request. Don't commit inside loops. Anything that reads then writes
  shared data (such as stock) must be safe under concurrent requests.
- Money uses `Decimal` / `Numeric`, never `float` arithmetic.
- Status codes: 400 broken business rule, 401 not authenticated, 403 wrong role or
  owner, 404 not found, 409 conflict (state or stock), 422 schema validation (FastAPI's
  default). Error `detail` messages say what went wrong in plain words.
- Secrets and settings come from `core/config.py` (environment). Never hard-code them.
- Use parameterised queries only. No SQL built from strings.

**TypeScript / React**
- Strict types, no `any` (replace existing ones in files you touch).
- `src/types/index.ts` mirrors the backend schemas. Change both together.
- All HTTP goes through `src/api/client.ts`.
- Derive state instead of syncing it with effects. Show loading, error and empty states.

**Tests**
- Backend: pytest with FastAPI's `TestClient`, against PostgreSQL (not SQLite, because
  locking, constraints and enums behave differently). Each test runs on a clean database.
- Name tests after the behaviour (`test_customer_cannot_register_as_admin`).
- Cover the happy path, permission failures and edge cases for every changed endpoint.

### Self-review before opening the PR

- Read the whole diff top to bottom.
- If you introduce or change a convention, grep for every existing place it applies and
  update them all in the same PR, or list the ones left out and why.
- Re-run the definition-of-done checks after the last change, not before it.
- If a review of your PR finds an issue that could recur, add the general lesson to this
  file in a follow-up commit.

### Tracking progress

The shareable review page is a Claude artifact at
https://claude.ai/artifact/7iDiUNRkjJmhvcsDSq4sWu. Its fix tracker is the `ITEMS` array
in the page's script, and each item has a `status` of `open`, `review` or `fixed`.
Only sessions with the Artifact tool can update it. Other sessions skip this step and
say so in the PR.

- **When the PR is opened:** set the item to `status: "review"` with `pr: <number>`.
- **When the PR is merged:** set `status: "fixed"`, add a one-line `note`, update the
  "last updated" date, and rewrite any text on the page that described the old behaviour
  (role callout, interview answers, resume wording). At the start of each session, run
  `gh pr list --state merged` and catch up on any items merged since the last update.
- Always republish to the same URL. Never create a new artifact for this.
- If Claude memory is available, update the notes `pending-improvements` and
  `resume-claims` when a fix changes how the project should be described.

### Repository settings

- `main` is protected. Changes arrive only through pull requests, and force-pushes
  and deletion are blocked, for admins too.
- Squash merge is the only merge method. The PR title and description become the
  commit on `main`, so write them carefully.
- Once CI exists (#19), its job names are required status checks. Renaming a job means
  updating branch protection in the same PR, or every PR waits on a check that never runs.
