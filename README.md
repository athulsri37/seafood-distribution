# Seafood Distribution & Order Management Platform

A full-stack web application for managing seafood inventory, customer orders, and
distribution reporting across a multi-role supply chain (admins, distributors, and
customers).

## Overview

This platform models a real-world seafood distribution workflow: distributors
manage inventory and fulfill orders, customers browse available product and place
orders, and admins get visibility into sales performance and stock health through
a reporting dashboard.

## Features

- **Role-based access** — Admin, Distributor, and Customer roles with different
  permissions enforced at the API level
- **Order management** — customers create orders; distributors/admins move orders
  through a status pipeline (Pending → Confirmed → In Transit → Delivered), with
  automatic stock deduction/restoration
- **Inventory tracking** — per-product stock levels, configurable reorder
  thresholds, low-stock flagging, and warehouse location tracking
- **Reporting dashboard** — total revenue, order volume, order status breakdown,
  and top-selling products, visualized with charts
- **JWT authentication** — secure token-based auth with password hashing (bcrypt)

## Tech Stack

| Layer      | Technology                                      |
|------------|--------------------------------------------------|
| Frontend   | React 18, TypeScript, Vite, Tailwind CSS, Recharts, React Router |
| Backend    | Python, FastAPI, SQLAlchemy, Pydantic            |
| Database   | PostgreSQL                                       |
| Auth       | JWT (python-jose), bcrypt password hashing       |
| Deployment | Docker & Docker Compose                          |

## Architecture

```
seafood-distribution-platform/
├── backend/                # FastAPI service
│   ├── app/
│   │   ├── core/           # config, database session, security/JWT, auth deps
│   │   ├── models/         # SQLAlchemy models (User, Product, Order, OrderItem)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   └── routers/        # API route handlers (auth, products, orders, reports, users)
│   ├── seed.py             # demo data seeding script
│   └── requirements.txt
├── frontend/                # React + TypeScript SPA
│   └── src/
│       ├── api/            # Axios client with auth interceptor
│       ├── context/        # AuthContext (login/register/logout, token persistence)
│       ├── pages/          # Login, Register, Orders, Inventory, Reports, Users
│       └── components/     # Layout, ProtectedRoute, StatCard
└── docker-compose.yml       # Postgres + backend + frontend orchestration
```

## Getting Started

### Option 1: Docker (recommended)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API docs (Swagger): http://localhost:8000/docs

The backend container applies database migrations before it starts. After the
containers are up, seed demo data:

```bash
docker compose exec backend python seed.py
```

### Option 2: Run locally

**Backend**
```bash
# No PostgreSQL yet? Run one in Docker (pick any free port and your own password):
docker run -d --name seafood-dev-db --restart unless-stopped -p 5434:5432   -v seafood-dev-pgdata:/var/lib/postgresql/data   -e POSTGRES_USER=seafood -e POSTGRES_PASSWORD=<choose-a-password>   -e POSTGRES_DB=seafood_distribution postgres:16-alpine

cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # set DATABASE_URL (and a random JWT_SECRET_KEY) for your Postgres
alembic upgrade head            # create or update the database schema
python seed.py                  # optional: creates demo users & products
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

### Database migrations

The schema is managed with [Alembic](https://alembic.sqlalchemy.org/) (`backend/migrations/`).
The app no longer creates tables on startup.

```bash
cd backend
alembic upgrade head                                  # apply all migrations
alembic revision --autogenerate -m "add supplier"     # after changing a model; review the file
alembic downgrade -1                                  # undo the last migration
```

**Databases created before migrations existed** already have the tables from the first
migration. Mark them as being at that migration, then apply the rest:

```bash
alembic stamp 9974bc68bdcd    # the initial schema, which create_all() already built
alembic upgrade head          # applies every later migration
```

Don't use `alembic stamp head` for this: it would mark later migrations as applied
without running them.

### Running the tests

Backend tests run against a real PostgreSQL database, because order and stock rules
depend on PostgreSQL's locking and constraints. The suite refuses to start unless
`TEST_DATABASE_URL` is set, and it empties every table after each test, so always
point it at a throwaway database:

```bash
docker run --rm -d --name seafood-test-db -p 5433:5432 \
  -e POSTGRES_PASSWORD=test -e POSTGRES_DB=seafood_test postgres:16-alpine

cd backend
pip install -r requirements-dev.txt
TEST_DATABASE_URL=postgresql://postgres:test@localhost:5433/seafood_test pytest
# PowerShell: $env:TEST_DATABASE_URL="postgresql://postgres:test@localhost:5433/seafood_test"; pytest

docker stop seafood-test-db    # --rm deletes the container and its data
```

Tests marked `xfail` describe known bugs from [`docs/backlog.md`](docs/backlog.md).
When a fix makes one pass, pytest reports an error until the `xfail` marker is removed.

The frontend has no unit tests yet. `npm run build` type-checks and builds it.

GitHub Actions runs both on every pull request (`.github/workflows/ci.yml`).

### Demo accounts (after seeding)

| Role        | Email                     | Password        |
|-------------|----------------------------|------------------|
| Admin       | admin@seafoodco.com        | Admin123!        |
| Distributor | distributor@seafoodco.com  | Distributor123!  |
| Customer    | customer@example.com       | Customer123!     |

## API Endpoints (selected)

- `POST /api/auth/register` / `POST /api/auth/login` — authentication. Sign-up creates
  customer accounts only; asking for another role returns 403.
- `GET/POST /api/products` — inventory listing & creation
- `PATCH /api/products/{id}` — stock/price updates
- `GET/POST /api/orders` — order listing & creation. Stock is checked and deducted
  atomically, so simultaneous orders can't oversell; an order that asks for more than is
  in stock returns 409 and saves nothing.
- `PATCH /api/orders/{id}/status` — order status transitions
- `GET /api/reports/dashboard` — aggregated sales & inventory metrics
- `GET/POST /api/users` — list users and create an account with any role (admin only)
- `PATCH /api/users/{id}/role` — change a user's role (admin only; admins can't remove
  their own admin role)

Full interactive API documentation is available at `/docs` once the backend is running.

## Notes

This project was rebuilt from the ground up as a modern reference implementation of
a seafood distribution and order management system, using a stack chosen to reflect
current industry practices (typed frontend, async-ready Python backend, containerized
deployment).
