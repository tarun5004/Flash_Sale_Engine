# Flash Sale Engine — Project Overview

> A technical onboarding document for backend engineers.

---

## What Problem Does This Project Solve?

E-commerce platforms occasionally run **time-limited sales** with heavily discounted products and limited inventory. These events create traffic patterns that differ fundamentally from normal operations:

| Normal Traffic | Flash Sale Traffic |
|----------------|-------------------|
| Spread throughout the day | Concentrated in seconds |
| 100-1000 requests/minute | 10,000-100,000 requests/second |
| Stock rarely exhausted | Stock depletes in seconds |
| Payment failures are rare edge cases | Payment failures happen at scale |
| Users browse casually | Users compete aggressively |

Standard e-commerce backends are not designed for this. They fail in predictable ways:

1. **Overselling** — 100 users buy the last 1 item (race condition)
2. **Database collapse** — Connection pool exhausted under load
3. **Inconsistent state** — Payment succeeds but order fails, or vice versa
4. **Poor user experience** — Timeouts, errors, confusion

This project builds a backend specifically designed to handle flash sale conditions while maintaining data integrity and acceptable user experience.

---

## What Is a Flash Sale System?

A flash sale system is a specialized order processing engine optimized for:

### High Concurrency
Thousands of users attempting to purchase the same limited-stock item simultaneously. The system must serialize access to inventory without creating unacceptable wait times.

### Strict Inventory Accuracy
Zero tolerance for overselling. If 100 units exist, exactly 100 orders can succeed. Not 101. Not 99 (unless cancelled).

### Atomic Transactions
Stock decrement, order creation, and payment must succeed or fail together. Partial states (stock decremented but no order, or order created but stock not decremented) are unacceptable.

### Graceful Degradation
When demand exceeds capacity, the system should fail predictably (reject excess requests cleanly) rather than unpredictably (corrupt data, crash, or hang).

### Fair Access
Users who arrive first should generally be served first. The system should not favor users with faster connections or those who spam refresh.

---

## High-Level System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FLASH SALE FLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐                                                       │
│  │   User   │                                                       │
│  └────┬─────┘                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐    ┌─────────────┐                                   │
│  │  Browse  │───▶│  Product    │  Read-only, cacheable             │
│  │ Products │    │  Listings   │                                   │
│  └────┬─────┘    └─────────────┘                                   │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐    ┌─────────────┐                                   │
│  │  Click   │───▶│  Rate       │  Reject if too many requests      │
│  │  "Buy"   │    │  Limiter    │                                   │
│  └────┬─────┘    └─────────────┘                                   │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐    ┌─────────────┐                                   │
│  │  Check   │───▶│  Stock      │  Atomic check + reserve           │
│  │  Stock   │    │  Service    │  Fail fast if unavailable         │
│  └────┬─────┘    └─────────────┘                                   │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐    ┌─────────────┐                                   │
│  │  Create  │───▶│  Order      │  Status: PENDING                  │
│  │  Order   │    │  Service    │  Stock: Reserved                  │
│  └────┬─────┘    └─────────────┘                                   │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐    ┌─────────────┐                                   │
│  │  Process │───▶│  Payment    │  External gateway                 │
│  │  Payment │    │  Service    │  Async confirmation               │
│  └────┬─────┘    └─────────────┘                                   │
│       │                                                             │
│       ├─── Success ───▶  Order: PAID, Stock: Committed             │
│       │                                                             │
│       └─── Failure ───▶  Order: FAILED, Stock: Released            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Flow Breakdown

| Step | Component | Responsibility |
|------|-----------|----------------|
| 1 | **API Gateway / Router** | Receive HTTP request, authenticate user, route to service |
| 2 | **Rate Limiter** | Reject requests exceeding per-user or global limits |
| 3 | **Stock Service** | Atomically check availability and reserve inventory |
| 4 | **Order Service** | Create order record with PENDING status |
| 5 | **Payment Service** | Integrate with external payment gateway |
| 6 | **Webhook Handler** | Receive payment confirmation, finalize order |
| 7 | **Compensation Handler** | Restore stock if payment fails or times out |

### Critical Invariants

These must hold true at all times:

```
1. available_stock >= 0                    (never negative)
2. available_stock + reserved_stock = total_stock
3. count(PAID orders) <= initial_stock     (no overselling)
4. Every stock decrement has exactly one order
5. Every PAID order has exactly one successful payment
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **API Framework** | FastAPI | Async HTTP handling, automatic OpenAPI docs |
| **ORM** | SQLAlchemy (async) | Database abstraction, migration support |
| **Database** | PostgreSQL (prod) / SQLite (dev) | Persistent storage with ACID guarantees |
| **Cache** | Redis | Stock caching, rate limiting, distributed locks |
| **Task Queue** | Celery | Background job processing (payments, emails) |
| **Auth** | JWT (python-jose) | Stateless authentication |

---

## Project Structure

```
Flash_Sale_Engine/
│
├── app/
│   ├── main.py              # Application factory, FastAPI instance
│   ├── core/
│   │   ├── config.py        # Environment-based configuration
│   │   └── events.py        # Startup/shutdown lifecycle hooks
│   │
│   ├── models/              # SQLAlchemy ORM models (database schema)
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── user.py
│   │   └── payment.py
│   │
│   ├── schemas/             # Pydantic models (API request/response)
│   │   ├── product_schema.py
│   │   ├── order_schema.py
│   │   └── user_schema.py
│   │
│   ├── repositories/        # Database access layer (queries only)
│   │   ├── product_repo.py
│   │   ├── order_repo.py
│   │   └── user_repo.py
│   │
│   ├── services/            # Business logic layer
│   │   └── product_service.py
│   │
│   ├── routers/             # HTTP endpoint definitions
│   │   └── products.py
│   │
│   └── db/
│       ├── base.py          # SQLAlchemy Base class
│       └── session.py       # Database connection management
│
├── planning/                # Architecture decisions, TODOs
│   ├── PHASED_TODO.md
│   ├── FUTURE_IMPROVEMENTS.md
│   └── deep_dives/          # Detailed technical analysis
│
├── docs/                    # Documentation
│   └── PROJECT_OVERVIEW.md  # This file
│
├── security.py              # JWT utilities, password hashing
├── requirements.txt         # Python dependencies
└── AI_CONTEXT.md           # Guidelines for AI-assisted development
```

### Layered Architecture

```
┌─────────────────────────────────────────┐
│              Routers                    │  ← HTTP interface
│         (products.py, etc.)             │
├─────────────────────────────────────────┤
│              Services                   │  ← Business logic
│        (product_service.py)             │
├─────────────────────────────────────────┤
│            Repositories                 │  ← Data access
│         (product_repo.py)               │
├─────────────────────────────────────────┤
│              Models                     │  ← Database schema
│           (product.py)                  │
├─────────────────────────────────────────┤
│              Database                   │  ← PostgreSQL/SQLite
└─────────────────────────────────────────┘
```

**Rules:**
- Routers call Services (never Repositories directly)
- Services call Repositories (never raw SQL)
- Repositories return ORM objects (not dicts)
- Each layer has single responsibility

---

## Non-Goals

This system intentionally does NOT handle:

### 1. Product Catalog Management
This is not a full e-commerce platform. We assume:
- Products are created by a separate admin system or scripts
- Product descriptions, SEO, and rich media are managed elsewhere
- We only store fields necessary for transactions (name, price, stock)

### 2. Shipping and Fulfillment
Post-order logistics are out of scope:
- No shipping address validation
- No carrier integration
- No delivery tracking
- These would be handled by separate fulfillment services

### 3. Customer Support Features
We do not include:
- Live chat
- Ticket management
- Refund processing UI
- Return merchandise authorization (RMA)

### 4. Analytics and Reporting
Business intelligence is not in scope:
- No sales dashboards
- No conversion funnels
- No A/B testing infrastructure
- Logs can be exported to dedicated analytics platforms

### 5. Multi-Tenancy
This is a single-tenant system:
- One database, one set of products
- No organization/team isolation
- No per-tenant configuration

### 6. Internationalization
No multi-region or multi-currency support:
- Single currency (assumed INR or USD)
- Single language
- Single timezone for all timestamps
- No tax calculation by region

### 7. Complex Promotions Engine
Limited discount capabilities:
- Simple percentage discounts only
- No BOGO (buy one get one)
- No cart-level discounts
- No coupon codes
- No tiered pricing

### 8. Fraud Detection
We rely on payment gateways for fraud:
- No velocity checks
- No device fingerprinting
- No address verification service (AVS)
- No machine learning risk scoring

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Product CRUD | ✅ Complete | Create, update, list, search, soft delete |
| User Authentication | ⬜ Not Started | JWT utilities exist, endpoints missing |
| Order Placement | ⬜ Not Started | Model exists, service/router missing |
| Stock Locking | ⬜ Not Started | FOR UPDATE query exists, not integrated |
| Payment Integration | ⬜ Not Started | Model exists, no gateway integration |
| Redis Caching | ⬜ Not Started | Configured, not implemented |
| Background Jobs | ⬜ Not Started | Celery in requirements, not set up |

See [planning/PHASED_TODO.md](../planning/PHASED_TODO.md) for detailed roadmap.

---

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 13+ (or SQLite for development)
- Redis 6+

### Local Setup
```bash
# Clone repository
git clone <repo-url>
cd Flash_Sale_Engine

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run development server
uvicorn app.main:app --reload
```

### API Documentation
Once running, access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Key Decisions

### Why FastAPI?
- Native async support (critical for I/O-bound flash sale workloads)
- Automatic OpenAPI documentation
- Pydantic integration for request validation
- Growing ecosystem and community

### Why PostgreSQL?
- Row-level locking (FOR UPDATE) essential for stock management
- ACID compliance required for financial transactions
- JSON support for flexible audit logging
- Proven at scale by major e-commerce platforms

### Why Repository Pattern?
- Testability: Mock repository in tests without database
- Flexibility: Change database without touching services
- Single responsibility: Queries isolated from business logic

### Why Not Microservices?
- Startup context: Team size and operational overhead don't justify microservices
- Transaction boundaries: Atomic stock + order + payment easier in monolith
- Future path: Can extract services later if needed

---

## Contributing

Before making changes:
1. Read [AI_CONTEXT.md](../AI_CONTEXT.md) for coding guidelines
2. Check [planning/PHASED_TODO.md](../planning/PHASED_TODO.md) for current priorities
3. Review [planning/FUTURE_IMPROVEMENTS.md](../planning/FUTURE_IMPROVEMENTS.md) for context on planned features

For complex features, read the relevant deep dive in `planning/deep_dives/` first.

---

## Questions?

If something is unclear or undocumented, that's a bug. Please:
1. Ask in team chat
2. Update this document with the answer
3. Future engineers will thank you
