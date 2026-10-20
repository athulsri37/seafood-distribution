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

Roles are `ADMIN`, `DISTRIBUTOR` and `CUSTOMER`. Sign-up creates customers only. Admins
create staff accounts and change roles through `/api/users`, and can't remove their own
admin role. The backend is the only place permissions are enforced (`require_roles()`
in `core/deps.py`, plus inline ownership checks). Frontend checks only hide UI.

Order statuses follow `ALLOWED_TRANSITIONS` in `app/services/orders.py`: one step at a time,
cancel (which restores stock) only before IN_TRANSIT, and DELIVERED and CANCELLED are final.
The API returns each order's `next_statuses`, and the frontend offers only those. Change
the rules in that one map, never in the router or the UI.

Reports treat cancelled orders as never sold: revenue, order totals and top products filter
with `NOT_CANCELLED` in `app/routers/reports.py`; only the status breakdown includes them.
Any new sales figure must use the same filter.

### Running locally

```bash
# Backend (from backend/)
python -m venv venv && venv\Scripts\activate      # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                              # DATABASE_URL and JWT_SECRET_KEY are required
alembic upgrade head                              # create or update the schema
python seed.py                                    # demo users and products
uvicorn app.main:app --reload                     # http://localhost:8000/docs

# Frontend (from frontend/)
npm install
npm run dev                                       # http://localhost:5173, proxies /api → :8000
```

`seed.py` prints the demo logins with random passwords; `--reset-demo-passwords` replaces them.

### Running the tests

```bash
docker run --rm -d --name seafood-test-db -p 5433:5432 \
  -e POSTGRES_PASSWORD=test -e POSTGRES_DB=seafood_test postgres:16-alpine
cd backend && pip install -r requirements-dev.txt
TEST_DATABASE_URL=postgresql://postgres:test@localhost:5433/seafood_test pytest
cd ../frontend && npm ci && npm run build      # type-check and build
docker stop seafood-test-db
```

The suite exits with code 4 if `TEST_DATABASE_URL` is unset. That's deliberate: it
truncates every table after each test.

### Known traps (until their backlog items are fixed)

- `bcrypt` is pinned to 4.0.1 because passlib 1.7.4 breaks on newer versions (hashing
  raises `ValueError` on 5.x). Don't unpin it without replacing passlib.
- Pydantic models still use the v1-style `class Config`, which prints deprecation
  warnings in test runs (B23). They're expected until that item is fixed.

## Backlog

`docs/backlog.md` is the source of truth for the fix items. Each has a stable ID: `B1`, `B2`, and so on.
Always write item IDs as `B<n>`, never `#<n>`: on GitHub, `#<n>` links to pull request or
issue n, so `#2` would point at the wrong thing.
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
Add it to `docs/backlog.md` as a new item and mention it in the PR. The one exception
is a problem that blocks the item (for example, tests can't run at all). Fix that in
the same branch, add it to the backlog as fixed by this PR, and explain it under
"Decisions I made".

Several open PRs that each delete a bullet from the same short list (such as "Known
traps" below) conflict, because their deletions touch adjacent lines. Resolve by keeping
every deletion and every addition from both sides, then check no fixed item's bullet
survived.

If your branch needs another open PR's changes, merge that PR's branch into yours,
say so under "Interactions with open PRs", and ask for the other PR to be merged first.
After it's squash-merged, merge `origin/main` into your branch so the diff shrinks
back to your own changes. Because the squash commit isn't an ancestor of your branch,
any file both PRs changed reports an add/add conflict. First confirm that `main` holds
exactly the other PR's content (`git diff <its last commit> origin/main` prints nothing).
Then keep your side (`git checkout --ours <files>`), and check that the merge commit's
tree matches your branch's tree from before the merge. Never force-push to avoid this.

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
- Before pushing a follow-up to a PR's branch, check it's still open
  (`gh pr view <n> --json state`). If it's already merged, put the follow-up on a new
  branch from `origin/main` and open a new PR. Commits pushed after a merge never reach
  `main`, and GitHub silently stops running CI for them.
- PR title: `B<n>: <summary>` (for example, `B1: Stop self-registration as admin`).
- PR body sections: **Problem**, **Fix**, **Decisions I made**, **Behaviour/API changes**,
  **Interactions with open PRs**, **Testing**, **Not tested**.

### Passwords and secrets

- Never write a password, token, key or connection-string password into anything that
  reaches GitHub: commits, PR titles and descriptions, comments, `docs/backlog.md` or
  test data. This includes the demo logins: their passwords are random and printed by
  `seed.py`, so refer to them as "the demo admin login", never by value.
- Test accounts use obviously fake, test-only passwords (as in `tests/helpers.py`), never
  a real or demo password.
- `.env` files are kept out of git (`.gitignore`) and out of Docker images
  (`backend/.dockerignore`, `frontend/.dockerignore`). When you add a file that holds
  secrets or host-specific build output, add it to all three.
- Before pushing, search the diff and the PR description for the demo passwords and
  for strings like `password=`, `secret` and `token`.

### Attribution

- No `Co-authored-by`, `Claude-Session`, "Generated with Claude Code" or session links in
  commits or PR bodies.
- Check before pushing:
  `git log origin/main..HEAD --format=%B | grep -iE "co-authored-by|generated with|claude-session|claude\.ai/code"`
  must print nothing. Apply the same check to the PR description. The `attribution`
  workflow repeats both checks on every PR and whenever its description is edited.

### Definition of done (all of these, every PR)

1. **Backend tests:** `pytest` from `backend/` passes, and the PR adds tests that fail
   without the fix and pass with it. If the item has an `xfail` test, remove the marker:
   it is the first test the fix has to pass.
2. **Frontend checks:** `npm run build` from `frontend/` (runs `tsc` and the Vite build)
   passes with no new type errors.
3. **Real API against a throwaway database,** covering success and error paths
   (wrong role → 403, bad input → 422, and so on):
   ```bash
   docker run --rm -d --name seafood-test-db -p 5433:5432 \
     -e POSTGRES_PASSWORD=test -e POSTGRES_DB=seafood_test postgres:16-alpine
   # DATABASE_URL=postgresql://postgres:test@localhost:5433/seafood_test
   # DATABASE_URL=... alembic upgrade head && python seed.py, then run the API on
   # port 8010 and exercise it with curl or httpx. Finally:
   docker stop seafood-test-db                       # --rm deletes it
   ```
   Never point tests at the development database or the Compose `pgdata` volume.
4. **Visible changes:** any change a customer, distributor or admin can see is checked
   in a browser (Playwright) for every affected role, including loading, error and empty
   states (fake them with `page.route`). Run the API on 8010 and the frontend with
   `API_PROXY_TARGET=http://localhost:8010 npx vite --port 5183 --strictPort`. Install
   Playwright outside the repo (for example, in a scratch folder) until the project adds
   it as a dev dependency, and give test records unique names so the script can be re-run.
5. **Docker changes:** if you touch a Dockerfile, a `.dockerignore` or
   `docker-compose.yml`, bring the stack up with a throwaway project name and `.env`
   (`docker compose -p seafood-check up -d --build`), check the API health, the frontend
   and `/api` through the frontend, then remove it all (`down -v --rmi local`) and delete
   that `.env`.
6. **Ports:** use non-default ports (API 8010, test Postgres 5433, Vite 5183). Never stop
   a process you didn't start.
7. **Docs:** update `README.md` and this file when you change an endpoint, a command,
   an environment variable or a convention.
8. **Backlog:** mark the item fixed in `docs/backlog.md` with a one-line note.
9. **PR write-up:** the Testing section lists what ran, with results. "Not tested" says
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
- Input schemas must reject anything the database would refuse, so bad input is a 422
  naming the field, never a 500. That means bounds that match the column (see `Price` and
  `Count` in `schemas/product.py`), `min_length=1` for required text, and
  `str_strip_whitespace=True`. For partial updates (PATCH), reject explicit `null` for
  NOT NULL columns with a `field_validator`: it only runs for fields the request sent.
- New schemas use Pydantic v2's `model_config = ConfigDict(...)`, not `class Config` (B23).
- Commit once per request. Don't commit inside loops. Anything that reads then writes
  shared data (such as stock) must be safe under concurrent requests:
  - Change counters in SQL, never in Python: a conditional
    `update(Product).where(..., Product.quantity_on_hand >= n).values(quantity_on_hand=Product.quantity_on_hand - n)`,
    or `+ n` to restore. Reading the row and assigning a new value loses concurrent updates.
  - When one request changes several rows, touch them in a fixed order (by id) so two
    requests can't deadlock.
  - Lock a row with `.with_for_update()` when a decision depends on its current state
    (for example, "only restore stock if the order isn't already cancelled").
  - Back invariants with a database constraint as well (`quantity_on_hand >= 0`).
  - Test them with `send_simultaneously()` in `tests/helpers.py`, which fires real
    concurrent requests at the API (examples in `tests/test_order_concurrency.py`).
- Money uses `Decimal` / `Numeric`, never `float` arithmetic.
- Status codes: 400 broken business rule, 401 not authenticated, 403 wrong role or
  owner, 404 not found, 409 conflict (state or stock), 422 schema validation (FastAPI's
  default). Error `detail` messages say what went wrong in plain words.
- Secrets and settings come from `core/config.py` (environment). Never hard-code them, and
  never give a credential a default value: the app must refuse to start without it.
  `tests/conftest.py` sets test-only values before importing the app.
- `create_app()` in `app/main.py` builds the app from `settings`. To test behaviour that
  depends on a setting (for example CORS), monkeypatch `settings` and call `create_app()`.
- Cross-origin access is off unless `CORS_ORIGINS` lists origins. Never allow `*` or
  credentials: logins use the Authorization header, not cookies.
- Use parameterised queries only. No SQL built from strings.

**Database changes**
- Every model change ships with an Alembic migration in the same PR:
  `alembic revision --autogenerate -m "<what changed>"`, then read and tidy the file.
  Autogenerate misses some things (data migrations, renamed columns, enum value changes,
  dropping enum types in `downgrade`), so write those by hand.
- Every migration must downgrade cleanly. `tests/test_migrations.py` checks that the
  models match the migrations, that there's a single head, and that downgrade-then-upgrade
  works, so CI fails on drift.
- Never edit a migration that's already on `main`. Add a new one.
- Instructions that say `head` change meaning whenever a migration is added. Docs for
  adopting an old database must name the baseline revision (`alembic stamp 9974bc68bdcd`),
  never `stamp head`, which would skip every later migration.
- Constraint names follow `NAMING_CONVENTION` in `app/core/database.py`. Check
  constraints need an explicit `name=`.
- Import `app.models` (the package) wherever the full schema is needed. It registers
  every model, which relationships by name rely on.
- The app never creates tables itself. Locally run `alembic upgrade head`; the backend
  Docker image runs it before starting.

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
- Fixtures live in `tests/conftest.py` (`client`, `db`, `make_user`, `make_product`,
  `auth_headers`, and `admin` / `distributor` / `customer`). Plain helpers and shared
  types live in `tests/helpers.py`. Never import from `conftest.py`.
- A known bug that isn't being fixed yet can get a test marked
  `@pytest.mark.xfail(reason="B<n>: <what's wrong>")`. `xfail_strict` is on, so the
  run fails as soon as a fix makes it pass, and the fix's PR has to remove the marker.
  Check with `pytest --runxfail` that it fails on the bug's assertion, not on an error.
- Role rules are tested as a matrix in `tests/test_permissions.py`. When an endpoint
  or role rule changes, update the matrix.

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

- `main` is protected. Changes arrive only through pull requests, history stays linear,
  conversations must be resolved, and force-pushes and deletion are blocked, for admins too.
  No approving review is required: the owner is the only maintainer and GitHub doesn't
  let you approve your own PR, so the owner merging is the review.
- Squash merge is the only merge method. The PR title and description become the
  commit on `main`, so write them carefully.
- Required status checks are the job names `backend` and `frontend` (in
  `.github/workflows/ci.yml`) and `attribution` (in `.github/workflows/attribution.yml`).
  Renaming a job means updating branch protection in the same PR, or every PR waits on
  a check that never runs.
