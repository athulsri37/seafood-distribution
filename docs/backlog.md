# Backlog

Fix items from the code review of 8 October 2026. Numbers are stable: don't renumber.
Add new items at the end. When an item is fixed, change its status to `Fixed (#PR)`
and add a one-line note.

Priority items are the ones the resume claims depend on. Do them first.

| #  | Area        | Problem | Fix | Status |
|----|-------------|---------|-----|--------|
| 1  | Priority    | Anyone can sign up as an admin: `auth.py` saves the requested role, and `Register.tsx` offers Admin in a dropdown. | Force self-registration to `CUSTOMER`, remove the dropdown, and add an admin-only endpoint to create or promote staff. | Open |
| 7  | Priority    | Two orders at the same moment can oversell stock: `create_order` reads and then decrements with no lock. | Conditional `UPDATE … SET qty = qty − n WHERE qty >= n` (or `SELECT … FOR UPDATE` in product-id order), plus `CHECK (quantity_on_hand >= 0)`. | Open |
| 8  | Priority    | Order status can change in any direction. `CANCELLED → PENDING` doesn't take the stock off again, and cancelling a `DELIVERED` order restores stock that has shipped. | Allow only valid transitions and return 409 otherwise. | Open |
| 2  | Security    | Compose sets `JWT_SECRET` but `config.py` reads `JWT_SECRET_KEY`, so the default secret is used. | Use one variable name and refuse to start with the default secret outside development. | Open |
| 3  | Security    | The JWT is stored in `localStorage`, where injected scripts can read it. | Consider an httpOnly cookie with CSRF protection. | Open |
| 4  | Security    | No refresh tokens or revocation. Tokens live 60 minutes, even after logout. | Short-lived access tokens with refresh tokens, or a denylist. | Open |
| 5  | Security    | CORS allows `*` with credentials (`main.py`). | Allow only configured frontend origins. | Open |
| 6  | Security    | Customers can see warehouse locations and exact stock levels. | Return a customer-facing product schema without internal fields. | Open |
| 9  | Correctness | The stock ±10 buttons send a total calculated in the browser, so concurrent clicks lose updates (`Inventory.tsx`). | Send the change and apply it on the server. | Open |
| 10 | Correctness | `ProductUpdate` has no validation, so negative prices or stock are accepted. | Add `gt=0` / `ge=0` rules. | Open |
| 11 | Correctness | Deleting a product that has been ordered fails with a 500 (foreign key). | Soft delete with an `is_active` flag. | Open |
| 12 | Correctness | Order totals are added up as `float`. | Use `Decimal` throughout. | Open |
| 13 | Correctness | Report revenue includes cancelled orders. | Exclude `CANCELLED` from revenue. | Open |
| 14 | Performance | N+1 queries when listing orders. | `selectinload` / `joinedload`. | Open |
| 15 | Performance | No pagination on orders, products or users. | Limit/offset or cursor pagination. | Open |
| 16 | Performance | Low-stock filtering and counting run in Python. | Do it in SQL. | Open |
| 17 | Engineering | `docker compose up` is broken: the backend publishes 4000 but listens on 8000, and the Vite proxy targets `localhost:8000` inside the container. | Fix the port, and make the proxy target configurable (`API_PROXY_TARGET`). | Open |
| 18 | Engineering | Alembic is installed but unused; `create_all()` never alters existing tables. | Add Alembic migrations. | Open |
| 19 | Engineering | No tests. | pytest harness on PostgreSQL, plus CI. | Open |
| 20 | Engineering | Swagger's Authorize button fails: `tokenUrl` points to a JSON login. | Accept `OAuth2PasswordRequestForm` or add a form-based token endpoint. | Open |
| 21 | Engineering | Missing screens: no create or delete product in the UI, and no single-order view. | Add them. | Open |
