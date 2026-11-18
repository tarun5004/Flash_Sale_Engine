# Flash Sale Engine

**A FastAPI commerce backend exploring stock locking, order transactions and payment-failure compensation.**

The project separates HTTP routes, services and repositories so transaction ownership and failure handling stay visible. It includes a separate HTML/CSS/JavaScript storefront prototype.

## Implemented backend

- Product catalog, stock and price operations through async SQLAlchemy repositories.
- JWT-based login and authenticated cart/order endpoints.
- An order service that requests a product row lock, checks stock, creates an order and commits the result in one transaction.
- A deterministic fake payment gateway: every fifth order fails, exercising stock restoration and a persisted failed order.
- Interactive FastAPI API documentation and a development-only product seeder.

```text
FastAPI routes -> services -> repositories -> async SQLAlchemy database
                      |
                      +-> simulated payment result -> commit or rollback
```

## Two separate demo paths

| Path | What it exercises |
| --- | --- |
| FastAPI API | Backend models, authentication, product/cart/order logic and database transactions |
| `index.html` + `app.js` | Storefront interactions using simulated backend calls and browser storage |

The storefront is not wired end-to-end to the FastAPI API. Its UI behavior does not demonstrate backend stock locking or real payments.

## Stack

Python, FastAPI, Pydantic Settings, async SQLAlchemy, SQLite/PostgreSQL, JWT and a vanilla JavaScript frontend. Redis, Celery and Alembic appear in dependencies/plans, but background workers and a migration workflow are not integrated in the current startup path.

## Run locally

Use Python **3.10+** and an isolated development environment.

```bash
git clone https://github.com/tarun5004/Flash_Sale_Engine.git
cd Flash_Sale_Engine
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` in PowerShell, or `source .venv/bin/activate` on macOS/Linux, then install:

```bash
python -m pip install -r requirements.txt
```

Create an untracked `.env` at the repository root with development values:

```dotenv
APP_NAME=flashsale-engine
DEBUG=true
SECRET_KEY=replace-with-a-random-local-secret
DATABASE_URL=sqlite+aiosqlite:///./flashsale.db
REDIS_URL=redis://localhost:6379/0
```

Generate your own secret with `python -c "import secrets; print(secrets.token_hex(32))"`. `REDIS_URL` is required by settings even though the current startup does not initialize a Redis worker.

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API explorer: `http://127.0.0.1:8000/docs`.
- Mock storefront: `http://127.0.0.1:8000/static/index.html`.
- Optional development seed: `POST /seed/products` in the API explorer with `DEBUG=true`.

Startup creates model tables automatically. Use a disposable database: the seed and product-service script write data.

## Repository guide

| Directory | Responsibility |
| --- | --- |
| [`app/routers/`](app/routers/) | HTTP endpoints and dependencies |
| [`app/services/`](app/services/) | Business rules and transaction boundaries |
| [`app/repositories/`](app/repositories/) | Database queries, including the product lock |
| [`app/models/`](app/models/) | SQLAlchemy models |
| [`app/core/`](app/core/) | Settings, authentication dependencies and lifecycle |
| [`docs/`](docs/) | Architecture and module notes |
| [`planning/`](planning/) | Planned work and design exploration |

## Engineering boundaries

- PostgreSQL can enforce the requested `SELECT ... FOR UPDATE` row lock. SQLite is convenient for local exploration but does not provide equivalent row-locking semantics; no concurrent-overselling guarantee is claimed for the SQLite demo.
- Payments are simulated, not connected to a payment provider. Queue-based reservations, high-traffic capacity and load-test results are not demonstrated.
- The app currently mounts the project root at `/static`; keep it bound to localhost and do not treat this configuration as suitable for public deployment. CORS and development seeding also need deployment-specific review.
- `test_product_service.py` is a database-writing smoke script executed with `python test_product_service.py`, not an isolated pytest suite. It does not validate concurrency, payments or end-to-end UI integration.

## Design notes

[Architecture](docs/ARCHITECTURE.md) · [Modules](docs/MODULE_DOCUMENTATION.md) · [Database notes](docs/DATABASE_AND_MIGRATIONS.md) · [Stock locking](planning/deep_dives/01_STOCK_LOCKING.md)

Design documents include future goals; the implemented scope and limitations above describe the current code.
