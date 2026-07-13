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

After the containers are up, seed demo data:

```bash
docker compose exec backend python seed.py
```

### Option 2: Run locally

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # update DATABASE_URL to point at your local Postgres
python seed.py                  # optional: creates demo users & products
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

### Demo accounts (after seeding)

| Role        | Email                     | Password        |
|-------------|----------------------------|------------------|
| Admin       | admin@seafoodco.com        | Admin123!        |
| Distributor | distributor@seafoodco.com  | Distributor123!  |
| Customer    | customer@example.com       | Customer123!     |

## API Endpoints (selected)

- `POST /api/auth/register` / `POST /api/auth/login` — authentication
- `GET/POST /api/products` — inventory listing & creation
- `PATCH /api/products/{id}` — stock/price updates
- `GET/POST /api/orders` — order listing & creation (stock-aware)
- `PATCH /api/orders/{id}/status` — order status transitions
- `GET /api/reports/dashboard` — aggregated sales & inventory metrics

Full interactive API documentation is available at `/docs` once the backend is running.

## Notes

This project was rebuilt from the ground up as a modern reference implementation of
a seafood distribution and order management system, using a stack chosen to reflect
current industry practices (typed frontend, async-ready Python backend, containerized
deployment).
