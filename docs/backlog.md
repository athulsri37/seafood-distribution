# Backlog

Fix items from the code review of 8 October 2026.

- IDs are stable: never renumber, and add new items at the end.
- Write item IDs as `B<n>`. On GitHub, `#<n>` links to pull request n, so use `#<n>`
  only for pull requests.
- When an item is fixed, set its status to `Fixed (#<PR>)` with a one-line note.

Priority items are the ones the resume claims depend on. Do them first.

| ID  | Area        | Problem | Fix | Status |
|-----|-------------|---------|-----|--------|
| B1  | Priority    | Anyone can sign up as an admin: `auth.py` saves the requested role, and `Register.tsx` offers Admin in a dropdown. | Force self-registration to `CUSTOMER`, remove the dropdown, and add an admin-only endpoint to create or promote staff. | Fixed (#3): sign-up returns 403 for staff roles and the dropdown is gone; admins create accounts and change roles from the Users page, and can't remove their own admin role. |
| B7  | Priority    | Two orders at the same moment can oversell stock: `create_order` reads and then decrements with no lock. | Conditional `UPDATE … SET qty = qty − n WHERE qty >= n` (or `SELECT … FOR UPDATE` in product-id order), plus `CHECK (quantity_on_hand >= 0)`. | Open |
| B8  | Priority    | Order status can change in any direction. `CANCELLED → PENDING` doesn't take the stock off again, and cancelling a `DELIVERED` order restores stock that has shipped. | Allow only valid transitions and return 409 otherwise. | Open |
| B2  | Security    | Compose sets `JWT_SECRET` but `config.py` reads `JWT_SECRET_KEY`, so the default secret is used. | Use one variable name and refuse to start with the default secret outside development. | Open |
| B3  | Security    | The JWT is stored in `localStorage`, where injected scripts can read it. | Consider an httpOnly cookie with CSRF protection. | Open |
| B4  | Security    | No refresh tokens or revocation. Tokens live 60 minutes, even after logout. | Short-lived access tokens with refresh tokens, or a denylist. | Open |
| B5  | Security    | CORS allows `*` with credentials (`main.py`). | Allow only configured frontend origins. | Open |
| B6  | Security    | Customers can see warehouse locations and exact stock levels. | Return a customer-facing product schema without internal fields. | Open |
| B9  | Correctness | The stock ±10 buttons send a total calculated in the browser, so concurrent clicks lose updates (`Inventory.tsx`). | Send the change and apply it on the server. | Open |
| B10 | Correctness | `ProductUpdate` has no validation, so negative prices or stock are accepted. | Add `gt=0` / `ge=0` rules. | Open |
| B11 | Correctness | Deleting a product that has been ordered fails with a 500 (foreign key). | Soft delete with an `is_active` flag. | Open |
| B12 | Correctness | Order totals are added up as `float`. | Use `Decimal` throughout. | Open |
| B13 | Correctness | Report revenue includes cancelled orders. | Exclude `CANCELLED` from revenue. | Open |
| B14 | Performance | N+1 queries when listing orders. | `selectinload` / `joinedload`. | Open |
| B15 | Performance | No pagination on orders, products or users. | Limit/offset or cursor pagination. | Open |
| B16 | Performance | Low-stock filtering and counting run in Python. | Do it in SQL. | Open |
| B17 | Engineering | `docker compose up` is broken: the backend publishes 4000 but listens on 8000, and the Vite proxy targets `localhost:8000` inside the container. | Fix the port, and make the proxy target configurable (`API_PROXY_TARGET`). | Open. `API_PROXY_TARGET` was added in #3 for browser testing; the Compose port and the in-container proxy target are still wrong. |
| B18 | Engineering | Alembic is installed but unused; `create_all()` never alters existing tables. | Add Alembic migrations. | Open |
| B19 | Engineering | No tests. | pytest harness on PostgreSQL, plus CI. | Fixed (#2): 59 API tests on PostgreSQL, `xfail` tests for B1, B8 and B13, GitHub Actions for backend, frontend and attribution. Frontend unit tests are still to come. |
| B20 | Engineering | Swagger's Authorize button fails: `tokenUrl` points to a JSON login. | Accept `OAuth2PasswordRequestForm` or add a form-based token endpoint. | Open |
| B21 | Engineering | Missing screens: no create or delete product in the UI, and no single-order view. | Add them. | Open |
| B22 | Engineering | `bcrypt` wasn't pinned. A fresh install gets bcrypt 5.x, which breaks passlib 1.7.4, so every password hash raises `ValueError` (registration, login and `seed.py` all fail). | Pin `bcrypt==4.0.1`; later, replace passlib. | Fixed (#2): pinned, because the test suite couldn't run without it. Replacing passlib is still open. |
| B23 | Engineering | Pydantic schemas use the v1-style `class Config`, deprecated in v2 and removed in v3. | Switch to `model_config = ConfigDict(from_attributes=True)`. | Open |
| B24 | Engineering | The frontend Dockerfile uses Node 20, which reached end of life in April 2026. CI uses Node 22. | Move the Dockerfile to Node 22 LTS. | Open |
| B25 | Engineering | `seed.py` crashes on a clean database (`expression 'Order' failed to locate a name`) because it imports `User` and `Product` but not `Order`. The README's seeding step fails. | Import every model before using the session (for example, `import app.models.order`), and add a test that runs the seed script. | Open |
| B26 | Correctness | The Axios interceptor redirects to `/login` on every 401, including a failed login itself, so a wrong password probably reloads the login page and clears the "Invalid email or password" message (`frontend/src/api/client.ts`). Found by reading the code; not yet reproduced in a browser. | Skip the redirect for the login request (or when already on `/login`), and show the API's error message. | Open |
| B27 | Security | The demo logins (including the admin password) are published in `README.md` and shown on the login page, and `seed.py` creates them with fixed passwords. Anyone running a copy with seed data has a known admin login. The repo is public. | Remove the passwords from the README and login page; have `seed.py` read demo passwords from environment variables, or generate and print them; and refuse to seed outside development. | Open |
