# Flash Sale Engine — Module Documentation

> Internal engineering documentation for all system modules.
> Covers existing implementations and planned modules.

---

## Table of Contents

### Core Infrastructure
1. [app/main.py](#appmainpy)
2. [app/core/config.py](#appcoreconfigupy)
3. [app/core/events.py](#appcoreventspy)
4. [app/db/base.py](#appdbbasepy)
5. [app/db/session.py](#appdbsessionpy)

### Domain Models
6. [app/models/product.py](#appmodelsproductpy)
7. [app/models/product_image.py](#appmodelsproduct_imagepy)
8. [app/models/user.py](#appmodelsuserpy)
9. [app/models/order.py](#appmodelsorderpy)
10. [app/models/payment.py](#appmodelspaymentpy)

### Repositories
11. [app/repositories/base_repo.py](#apprepositoriesbase_repopy)
12. [app/repositories/product_repo.py](#apprepositoriesproduct_repopy)
13. [app/repositories/product_image_repo.py](#apprepositoriesproduct_image_repopy)
14. [app/repositories/user_repo.py](#apprepositoriesuser_repopy)
15. [app/repositories/order_repo.py](#apprepositoriesorder_repopy)

### Services
16. [app/services/product_service.py](#appservicesproduct_servicepy)
17. [app/services/user_service.py](#appservicesuser_servicepy) *(Planned)*
18. [app/services/order_service.py](#appservicesorder_servicepy) *(Planned)*
19. [app/services/payment_service.py](#appservicespayment_servicepy) *(Planned)*
20. [app/services/stock_service.py](#appservicesstock_servicepy) *(Planned)*

### Routers
21. [app/routers/products.py](#approutersproductspy)
22. [app/routers/auth.py](#approutersauthpy) *(Planned)*
23. [app/routers/orders.py](#approutersorderspy) *(Planned)*
24. [app/routers/webhooks.py](#approuterswebhookspy) *(Planned)*

### Schemas
25. [app/schemas/product_schema.py](#appschemasproduct_schemapy)
26. [app/schemas/product_image_schema.py](#appschemasproduct_image_schemapy)
27. [app/schemas/user_schema.py](#appschemasuser_schemapy)
28. [app/schemas/order_schema.py](#appschemasorder_schemapy)

### Security & Utilities
29. [security.py](#securitypy)
30. [app/core/dependencies.py](#appcoredependenciespy) *(Planned)*
31. [app/core/cache.py](#appcorecachepy) *(Planned)*
32. [app/core/rate_limiter.py](#appcorerare_limiterpy) *(Planned)*

---

## Core Infrastructure

---

### app/main.py

**Status:** ✅ Implemented

**Purpose:**
Application entry point and factory. Creates and configures the FastAPI application instance.

**Responsibilities:**
- Instantiate FastAPI app with metadata (title, debug mode)
- Register lifecycle event handlers (startup, shutdown)
- Mount all routers with appropriate prefixes
- Configure middleware (CORS, authentication) — *currently missing*

**What It Should NOT Do:**
- Define route handlers (belongs in routers)
- Contain business logic (belongs in services)
- Create database connections directly (use session module)
- Import models directly (circular import risk)

**Dependencies:**
- `app.core.config` — Application settings
- `app.core.events` — Lifecycle hooks
- `app.routers.*` — All route modules

**Current Implementation:**
```
create_app() factory pattern
├── FastAPI instance creation
├── Event registration via register_events()
└── Router mounting (products only)
```

**Future Evolution:**
- Add CORS middleware configuration
- Add authentication middleware
- Add request ID middleware for tracing
- Add exception handlers for custom exceptions
- Mount additional routers (auth, orders, webhooks)
- Add OpenAPI customization (tags, descriptions)

---

### app/core/config.py

**Status:** ✅ Implemented

**Purpose:**
Centralized configuration management using Pydantic settings. Single source of truth for all environment-based configuration.

**Responsibilities:**
- Load configuration from environment variables
- Load configuration from `.env` file as fallback
- Provide type-safe access to settings
- Validate required settings on startup

**What It Should NOT Do:**
- Contain business logic
- Have database or network calls
- Cache computed values (use separate cache module)
- Store secrets in code (use environment only)

**Dependencies:**
- `pydantic_settings.BaseSettings` — Settings management
- `.env` file — Local development configuration

**Current Implementation:**
```
Settings class with:
├── APP_NAME (str)
├── DEBUG (bool)
├── SECRET_KEY (str)
├── ALGORITHM (str)
├── ACCESS_TOKEN_EXPIRE_MINUTES (int)
├── DATABASE_URL (str)
└── REDIS_URL (str)
```

**Future Evolution:**
- Add validation for SECRET_KEY strength
- Add validation to reject DEBUG=True in production
- Add database pool configuration (pool_size, max_overflow)
- Add rate limiting configuration
- Add payment gateway credentials
- Add feature flags for gradual rollouts
- Add environment detection (dev/staging/prod)

---

### app/core/events.py

**Status:** ✅ Implemented

**Purpose:**
Application lifecycle management. Handles startup and shutdown sequences.

**Responsibilities:**
- Initialize database tables on startup
- Establish connection pools on startup
- Close connections gracefully on shutdown
- Log lifecycle events

**What It Should NOT Do:**
- Contain business logic
- Handle HTTP requests
- Define routes
- Perform data migrations (use Alembic)

**Dependencies:**
- `app.db.session.engine` — Database engine
- `app.db.base.Base` — SQLAlchemy declarative base

**Current Implementation:**
```
register_events(app):
├── @app.on_event("startup")
│   └── Create database tables
└── @app.on_event("shutdown")
    └── Placeholder for cleanup
```

**Future Evolution:**
- Initialize Redis connection pool on startup
- Initialize Celery app on startup
- Health check verification on startup
- Warm up caches with critical data
- Graceful worker shutdown on SIGTERM
- Close Redis connections on shutdown
- Cancel pending background tasks on shutdown

---

### app/db/base.py

**Status:** ✅ Implemented

**Purpose:**
SQLAlchemy declarative base class. Foundation for all ORM models.

**Responsibilities:**
- Provide base class for all models
- Centralize table naming conventions
- Define common mixins (if any)

**What It Should NOT Do:**
- Define specific model classes (belongs in models/)
- Contain query logic (belongs in repositories)
- Manage connections (belongs in session.py)

**Dependencies:**
- `sqlalchemy.orm.declarative_base` — Base factory

**Current Implementation:**
```
Base = declarative_base()
```

**Future Evolution:**
- Add common mixin classes:
  - `TimestampMixin` — created_at, updated_at
  - `SoftDeleteMixin` — deleted_at, is_deleted
  - `AuditMixin` — created_by, updated_by
- Add custom naming convention for constraints
- Add repr mixin for debugging

---

### app/db/session.py

**Status:** ✅ Implemented

**Purpose:**
Database connection and session management. Provides database access to the application.

**Responsibilities:**
- Create async database engine with connection pool
- Provide session factory for creating sessions
- Provide FastAPI dependency for request-scoped sessions
- Manage connection lifecycle

**What It Should NOT Do:**
- Define models (belongs in models/)
- Execute queries (belongs in repositories)
- Handle transactions (belongs in services)
- Store connection credentials (use config)

**Dependencies:**
- `app.core.config.settings` — Database URL
- `sqlalchemy.ext.asyncio` — Async engine and session

**Current Implementation:**
```
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(...)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

**Future Evolution:**
- Add explicit pool configuration:
  - pool_size=20
  - max_overflow=30
  - pool_timeout=30
  - pool_recycle=1800
- Add connection health checks
- Add query logging for debugging
- Add read replica support (separate read engine)
- Add connection retry logic
- Add metrics for pool utilization

---

## Domain Models

---

### app/models/product.py

**Status:** ✅ Implemented

**Purpose:**
Product entity definition. Represents items available for sale.

**Responsibilities:**
- Define product table schema
- Define relationships (images)
- Define constraints (not null, defaults)
- Define indexes for query optimization

**What It Should NOT Do:**
- Contain business logic (belongs in services)
- Execute queries (belongs in repositories)
- Validate input (belongs in schemas)
- Format output (belongs in schemas)

**Dependencies:**
- `app.db.base.Base` — Declarative base

**Current Schema:**
```
products:
├── id (PK, Integer)
├── name (String 255, indexed, not null)
├── price (Numeric 10,2, not null)
├── stock (Integer, default 0, not null)
├── is_active (Boolean, default True, not null)
├── created_at (DateTime, server default now)
├── updated_at (DateTime, server default now, on update now)
└── images (relationship → ProductImage)
```

**Future Evolution:**
- Add `reserved_stock` column for reservation pattern
- Add `version` column for optimistic locking
- Add `sku` column for inventory management
- Add `max_per_user` column for purchase limits
- Add composite index on (is_active, created_at) for listings
- Add flash sale specific fields:
  - `sale_start_time`
  - `sale_end_time`
  - `original_price` (to show discount)

---

### app/models/product_image.py

**Status:** ✅ Implemented

**Purpose:**
Product image entity. Supports multiple images per product.

**Responsibilities:**
- Define product_images table schema
- Define relationship back to product
- Store image URLs (not binary data)

**What It Should NOT Do:**
- Store actual image files (use CDN/S3)
- Validate URL format (belongs in schema)
- Handle image upload (separate service concern)

**Dependencies:**
- `app.db.base.Base` — Declarative base
- `app.models.product.Product` — Parent relationship

**Current Schema:**
```
product_images:
├── id (PK, Integer)
├── product_id (FK → products.id)
├── image_url (String, not null)
└── product (relationship → Product)
```

**Future Evolution:**
- Add `position` column for ordering
- Add `is_primary` flag for main image
- Add `alt_text` for accessibility
- Add soft delete support
- Add image type (thumbnail, full, zoom)

---

### app/models/user.py

**Status:** ✅ Implemented

**Purpose:**
User entity. Represents authenticated users of the system.

**Responsibilities:**
- Define users table schema
- Store authentication credentials (hashed)
- Store account status

**What It Should NOT Do:**
- Store plain text passwords
- Contain authentication logic (belongs in security.py)
- Contain authorization logic (belongs in dependencies)

**Dependencies:**
- `app.db.base.Base` — Declarative base

**Current Schema:**
```
users:
├── id (PK, Integer)
├── email (String 255, unique, indexed, not null)
├── hashed_password (String 255, not null)
├── is_active (Integer — should be Boolean)
└── created_at (DateTime, server default now)
```

**Known Issues:**
- `is_active` is Integer, should be Boolean

**Future Evolution:**
- Fix `is_active` type to Boolean
- Add `role` column (customer, admin)
- Add `email_verified` boolean
- Add `last_login` timestamp
- Add `failed_login_attempts` for security
- Add `locked_until` for account lockout
- Add relationship to addresses
- Add relationship to orders

---

### app/models/order.py

**Status:** ✅ Implemented

**Purpose:**
Order entity. Represents a purchase transaction.

**Responsibilities:**
- Define orders table schema
- Track order lifecycle (status)
- Link to user and product

**What It Should NOT Do:**
- Process payments (belongs in payment service)
- Modify stock (belongs in stock service)
- Send notifications (belongs in notification service)

**Dependencies:**
- `app.db.base.Base` — Declarative base
- `app.models.user.User` — Customer relationship
- `app.models.product.Product` — Item relationship

**Current Schema:**
```
orders:
├── id (PK, Integer)
├── user_id (FK → users.id, not null)
├── product_id (FK → products.id, not null)
├── quantity (Integer, not null)
├── total_amount (Numeric 10,2, not null)
├── status (Enum: PENDING, PAID, FAILED, not null)
├── created_at (DateTime, server default now)
├── user (relationship → User)
└── product (relationship → Product)

OrderStatus(Enum):
├── PENDING
├── PAID
└── FAILED
```

**Future Evolution:**
- Add `idempotency_key` (unique, for duplicate prevention)
- Add `updated_at` timestamp
- Add `paid_at` timestamp
- Add `failed_reason` for debugging
- Add `price_at_purchase` (snapshot, in case product price changes)
- Add more statuses:
  - CANCELLED
  - REFUNDED
  - EXPIRED (payment timeout)
- Add index on (user_id, created_at) for user history
- Add index on (status, created_at) for admin views
- Add relationship to payments

---

### app/models/payment.py

**Status:** ✅ Implemented

**Purpose:**
Payment entity. Records payment attempts and results.

**Responsibilities:**
- Define payments table schema
- Track payment status
- Store gateway reference for reconciliation

**What It Should NOT Do:**
- Store card details (PCI violation)
- Communicate with payment gateway (belongs in service)
- Modify order status (belongs in service)

**Dependencies:**
- `app.db.base.Base` — Declarative base
- `app.models.order.Order` — Order relationship

**Current Schema:**
```
payments:
├── id (PK, Integer)
├── order_id (FK → orders.id, not null)
├── provider (String 100, not null)
├── status (Enum: SUCCESS, FAILED, not null)
├── transaction_ref (String 255, nullable)
├── created_at (DateTime, server default now)
└── order (relationship → Order)

PaymentStatus(Enum):
├── SUCCESS
└── FAILED
```

**Future Evolution:**
- Add `amount` (for partial payments, refunds)
- Add `currency` (for multi-currency support)
- Add `gateway_response` (JSON, for debugging)
- Add `idempotency_key` (for webhook deduplication)
- Add more statuses:
  - PENDING
  - PROCESSING
  - REFUNDED
  - DISPUTED
- Add `refund_id` for tracking refunds
- Add index on transaction_ref for webhook lookups

---

## Repositories

---

### app/repositories/base_repo.py

**Status:** ✅ Exists (likely empty or minimal)

**Purpose:**
Base repository class with common CRUD operations.

**Responsibilities:**
- Provide generic create, read, update, delete methods
- Reduce boilerplate in specific repositories
- Standardize error handling for database operations

**What It Should NOT Do:**
- Contain domain-specific logic
- Handle transactions (caller responsibility)
- Validate input (schemas do this)

**Dependencies:**
- `sqlalchemy.ext.asyncio.AsyncSession` — Database session

**Current Implementation:**
Likely minimal or empty.

**Future Evolution:**
- Implement generic CRUD:
  - `create(entity)` → INSERT
  - `get_by_id(id)` → SELECT by PK
  - `get_all()` → SELECT all
  - `update(entity)` → UPDATE
  - `delete(id)` → DELETE
- Add generic `get_by_id_for_update()` with locking
- Add pagination helpers
- Add soft delete support

---

### app/repositories/product_repo.py

**Status:** ✅ Implemented

**Purpose:**
Data access layer for Product entity.

**Responsibilities:**
- Execute all product-related database queries
- Provide `FOR UPDATE` locking for concurrent access
- Handle pagination and search queries

**What It Should NOT Do:**
- Validate business rules (belongs in service)
- Commit transactions (caller responsibility)
- Format response data (belongs in schema)

**Dependencies:**
- `app.models.product.Product` — ORM model
- `sqlalchemy.ext.asyncio.AsyncSession` — Database session

**Current Implementation:**
```
ProductRepository:
├── create(product) → INSERT, flush, return
├── get_by_id_for_update(id) → SELECT FOR UPDATE
├── get_all_active() → SELECT WHERE is_active
├── search_active_products(keyword) → ILIKE search
├── search_active_products_multi(keywords) → OR search
└── get_active_products_paginated(offset, limit, keywords)
```

**Future Evolution:**
- Add `get_by_id(id)` without lock for reads
- Add `get_by_ids(ids)` for batch fetch
- Add `count_active()` for pagination metadata
- Add `decrement_stock(id, quantity)` atomic operation
- Add `increment_stock(id, quantity)` for refunds
- Add full-text search using PostgreSQL tsvector
- Add caching layer integration

---

### app/repositories/product_image_repo.py

**Status:** ✅ Exists

**Purpose:**
Data access layer for ProductImage entity.

**Responsibilities:**
- CRUD operations for product images
- Query images by product ID

**What It Should NOT Do:**
- Upload images to storage (separate concern)
- Validate image URLs (schema responsibility)

**Dependencies:**
- `app.models.product_image.ProductImage` — ORM model
- `sqlalchemy.ext.asyncio.AsyncSession` — Database session

**Future Evolution:**
- Add `get_by_product_id(product_id)` for listing
- Add `delete_by_product_id(product_id)` for bulk delete
- Add `reorder(product_id, image_ids)` for position management

---

### app/repositories/user_repo.py

**Status:** ✅ Implemented

**Purpose:**
Data access layer for User entity.

**Responsibilities:**
- User CRUD operations
- Lookup by email for authentication
- Lookup by ID for authorization

**What It Should NOT Do:**
- Verify passwords (belongs in security.py)
- Generate tokens (belongs in security.py)
- Check authorization (belongs in dependencies)

**Dependencies:**
- `app.models.user.User` — ORM model
- `sqlalchemy.ext.asyncio.AsyncSession` — Database session

**Current Implementation:**
```
UserRepository:
├── create(user) → INSERT, flush, return
├── get_by_email(email) → SELECT by email
└── get_by_id(user_id) → SELECT by ID
```

**Future Evolution:**
- Add `exists_by_email(email)` for registration check
- Add `update_last_login(user_id)` for tracking
- Add `increment_failed_attempts(user_id)` for security
- Add `lock_account(user_id, until)` for lockout
- Add `get_by_ids(ids)` for batch operations

---

### app/repositories/order_repo.py

**Status:** ✅ Implemented

**Purpose:**
Data access layer for Order entity.

**Responsibilities:**
- Order CRUD operations
- Query orders with relationships loaded
- Support for order history queries

**What It Should NOT Do:**
- Process payments (belongs in payment service)
- Modify stock (belongs in stock/order service)
- Send notifications (belongs in notification service)

**Dependencies:**
- `app.models.order.Order` — ORM model
- `sqlalchemy.ext.asyncio.AsyncSession` — Database session

**Current Implementation:**
```
OrderRepository:
├── create(order) → INSERT, flush, return
└── get_by_id(order_id) → SELECT with product eager load
```

**Future Evolution:**
- Add `get_by_idempotency_key(key)` for duplicate detection
- Add `get_by_user_id(user_id, limit, offset)` for history
- Add `get_pending_orders()` for timeout processing
- Add `update_status(order_id, status)` for state changes
- Add `get_by_id_for_update(order_id)` for locking
- Add `count_by_user_and_product(user_id, product_id)` for limits

---

## Services

---

### app/services/product_service.py

**Status:** ✅ Implemented

**Purpose:**
Business logic layer for product operations.

**Responsibilities:**
- Validate business rules for product operations
- Coordinate repository calls
- Manage transactions (commit/rollback)
- Apply domain-specific logic (discounts, activation)

**What It Should NOT Do:**
- Handle HTTP concerns (status codes, headers)
- Format responses (schemas do this)
- Execute raw SQL (repositories do this)

**Dependencies:**
- `app.repositories.product_repo.ProductRepository` — Data access
- `sqlalchemy.ext.asyncio.AsyncSession` — Transaction management

**Current Implementation:**
```
ProductService:
├── create_product(name, price, stock)
├── update_price(product_id, new_price)
├── apply_discount(product_id, discount_percent)
├── get_products(page, limit, search)
├── update_stock(product_id, new_stock)
├── update_name(product_id, new_name)
├── activate_product(product_id)
├── deactivate_product(product_id)
├── add_product_image(product_id, image_url)
└── Private validators:
    ├── _validate_name(name)
    ├── _validate_price(price)
    ├── _validate_stock(stock)
    ├── _validate_product_id(product_id)
    └── _validate_discount_percentage(percent)
```

**Future Evolution:**
- Extract stock operations to dedicated StockService
- Add bulk operations (create multiple products)
- Add soft delete with scheduled permanent delete
- Add product duplication feature
- Add audit logging for all mutations

---

### app/services/user_service.py

**Status:** ❌ Planned

**Purpose:**
Business logic for user management and authentication.

**Responsibilities:**
- User registration with validation
- Password hashing (delegate to security.py)
- Login validation
- Profile updates
- Account status management

**What It Should NOT Do:**
- Issue JWT tokens (security.py does this)
- Handle HTTP authentication (middleware/dependency)
- Store sessions (stateless JWT approach)

**Dependencies:**
- `app.repositories.user_repo.UserRepository` — Data access
- `security.py` — Password hashing, token generation

**Planned Implementation:**
```
UserService:
├── register(email, password) → validate, hash, create
├── authenticate(email, password) → verify, return user
├── get_by_id(user_id) → return user profile
├── update_profile(user_id, data) → update allowed fields
├── change_password(user_id, old, new) → verify old, set new
├── deactivate(user_id) → set is_active = False
└── Validators:
    ├── _validate_email_unique(email)
    └── _validate_password_strength(password)
```

---

### app/services/order_service.py

**Status:** ❌ Planned

**Purpose:**
Core flash sale business logic. Handles order placement with stock management.

**Responsibilities:**
- Orchestrate order creation with stock reservation
- Ensure atomic stock decrement + order creation
- Handle order status transitions
- Enforce purchase limits per user
- Coordinate with payment service

**What It Should NOT Do:**
- Process payments directly (delegate to payment service)
- Send notifications (delegate to notification service)
- Handle HTTP concerns

**Dependencies:**
- `app.repositories.order_repo.OrderRepository` — Data access
- `app.repositories.product_repo.ProductRepository` — Stock access
- `app.services.stock_service.StockService` — Stock operations
- `sqlalchemy.ext.asyncio.AsyncSession` — Transaction management

**Planned Implementation:**
```
OrderService:
├── place_order(user_id, product_id, quantity, idempotency_key)
│   ├── Check idempotency (return existing if duplicate)
│   ├── Validate user can purchase (limits, status)
│   ├── Reserve stock (with lock)
│   ├── Create order (PENDING)
│   ├── Commit transaction
│   └── Return order
├── confirm_order(order_id) → set status PAID
├── fail_order(order_id, reason) → set status FAILED, restore stock
├── cancel_order(order_id) → user-initiated cancel, restore stock
├── get_order(order_id, user_id) → return with auth check
├── get_user_orders(user_id, page, limit) → order history
└── expire_pending_orders() → scheduled job, timeout handling
```

**Critical Invariants:**
- Stock decrement and order creation in same transaction
- Never commit stock change without order
- Never create order without stock change
- Idempotency key checked before any mutation

---

### app/services/payment_service.py

**Status:** ❌ Planned

**Purpose:**
Payment gateway integration and payment lifecycle management.

**Responsibilities:**
- Create payment sessions with gateway
- Process webhook callbacks
- Handle payment status updates
- Trigger order status changes
- Manage refunds

**What It Should NOT Do:**
- Store card details
- Handle stock (order service does this)
- Directly modify order status (coordinate with order service)

**Dependencies:**
- `app.repositories.payment_repo.PaymentRepository` — Data access (planned)
- `app.services.order_service.OrderService` — Order status updates
- External: Payment gateway SDK (Razorpay/Stripe)

**Planned Implementation:**
```
PaymentService:
├── create_payment_session(order_id, amount)
│   ├── Create gateway session
│   ├── Store payment record (PENDING)
│   └── Return redirect URL
├── handle_webhook(payload, signature)
│   ├── Verify signature
│   ├── Check idempotency (already processed?)
│   ├── Update payment status
│   └── Call order_service.confirm_order() or fail_order()
├── verify_payment(payment_id) → poll gateway for status
├── initiate_refund(payment_id, amount) → gateway refund
└── Validators:
    └── _verify_webhook_signature(payload, signature)
```

---

### app/services/stock_service.py

**Status:** ❌ Planned

**Purpose:**
Dedicated service for inventory operations. Extracted from product service for clarity.

**Responsibilities:**
- Atomic stock decrement with validation
- Stock restoration on order failure
- Stock reservation pattern (if implemented)
- Stock level queries

**What It Should NOT Do:**
- Handle order creation (order service does this)
- Process payments
- Manage product metadata

**Dependencies:**
- `app.repositories.product_repo.ProductRepository` — Data access
- `sqlalchemy.ext.asyncio.AsyncSession` — Transaction management

**Planned Implementation:**
```
StockService:
├── reserve_stock(product_id, quantity) → lock, check, decrement
├── release_stock(product_id, quantity) → restore on failure
├── get_available_stock(product_id) → for display
├── check_availability(product_id, quantity) → boolean check
└── Atomic operations:
    └── _decrement_with_check(product_id, quantity)
        # UPDATE ... SET stock = stock - ? WHERE stock >= ?
```

---

## Routers

---

### app/routers/products.py

**Status:** ✅ Implemented

**Purpose:**
HTTP endpoint definitions for product operations.

**Responsibilities:**
- Define routes with path, method, response model
- Extract and validate request parameters
- Call appropriate service methods
- Handle exceptions and return proper HTTP status codes

**What It Should NOT Do:**
- Contain business logic (belongs in services)
- Execute database queries (belongs in repositories)
- Manage transactions (services do this)

**Dependencies:**
- `app.services.product_service.ProductService` — Business logic
- `app.db.session.get_db` — Database session dependency
- `app.schemas.product_schema.*` — Request/response models

**Current Endpoints:**
```
POST   /products              → create_product
PATCH  /products/{id}/price   → update_product_price
PATCH  /products/{id}/discount → apply_product_discount
GET    /products              → get_products (paginated, searchable)
PATCH  /products/{id}/stock   → update_product_stock
PATCH  /products/{id}/name    → update_product_name
PATCH  /products/{id}/activate → activate_product
PATCH  /products/{id}/deactivate → deactivate_product
POST   /products/{id}/images  → add_product_image
DELETE /products/{id}         → soft_delete_product
```

**Known Issues:**
- No authentication on any endpoint
- Duplicate route definition for GET /products

**Future Evolution:**
- Add authentication dependency to write endpoints
- Add admin role check to write endpoints
- Fix duplicate route definition
- Add rate limiting to read endpoints
- Add cache headers for read endpoints

---

### app/routers/auth.py

**Status:** ❌ Planned

**Purpose:**
Authentication endpoints for user registration and login.

**Responsibilities:**
- User registration endpoint
- Login endpoint returning JWT
- Token refresh endpoint
- Logout endpoint (optional for stateless JWT)

**What It Should NOT Do:**
- Hash passwords (security.py does this)
- Store sessions (stateless approach)
- Handle authorization (use dependencies)

**Dependencies:**
- `app.services.user_service.UserService` — Business logic
- `security.py` — Token generation
- `app.schemas.user_schema.*` — Request/response models

**Planned Endpoints:**
```
POST /auth/register → create user, return user data
POST /auth/login    → verify credentials, return JWT
POST /auth/refresh  → validate refresh token, return new JWT
POST /auth/logout   → blacklist token (optional)
GET  /auth/me       → return current user profile
```

---

### app/routers/orders.py

**Status:** ❌ Planned

**Purpose:**
Order management endpoints. Core flash sale functionality.

**Responsibilities:**
- Order placement endpoint
- Order history endpoints
- Order detail endpoint

**What It Should NOT Do:**
- Contain stock logic (belongs in services)
- Process payments directly (delegate to service)

**Dependencies:**
- `app.services.order_service.OrderService` — Business logic
- `app.core.dependencies.get_current_user` — Authentication
- `app.schemas.order_schema.*` — Request/response models

**Planned Endpoints:**
```
POST /orders              → place order (authenticated)
GET  /orders              → list user's orders (authenticated)
GET  /orders/{id}         → get order detail (authenticated, owner only)
POST /orders/{id}/cancel  → cancel pending order (authenticated)
```

---

### app/routers/webhooks.py

**Status:** ❌ Planned

**Purpose:**
Webhook handlers for external service callbacks.

**Responsibilities:**
- Receive payment gateway callbacks
- Verify webhook signatures
- Delegate processing to services
- Return acknowledgment quickly

**What It Should NOT Do:**
- Perform slow operations synchronously
- Expose internal errors to gateway
- Skip signature verification

**Dependencies:**
- `app.services.payment_service.PaymentService` — Payment processing
- External: Webhook signature verification

**Planned Endpoints:**
```
POST /webhooks/razorpay → handle Razorpay payment callbacks
POST /webhooks/stripe   → handle Stripe payment callbacks (future)
```

**Critical Requirements:**
- Always return 200 on successful processing
- Return 200 even if order already processed (idempotency)
- Return 401 on signature failure
- Log all webhook payloads for debugging
- Complete within gateway timeout (30s)

---

## Schemas

---

### app/schemas/product_schema.py

**Status:** ✅ Implemented

**Purpose:**
Pydantic models for product API request/response validation.

**Responsibilities:**
- Validate incoming request data
- Define response structure
- Convert ORM objects to JSON-serializable format

**What It Should NOT Do:**
- Contain business logic
- Access database
- Perform complex transformations

**Current Schemas:**
```
ProductCreateSchema:
├── name: str
├── price: Decimal
└── stock: int

ProductResponseSchema:
├── id: int
├── name: str
├── price: Decimal
├── stock: int
├── is_active: bool
├── created_at: datetime
└── updated_at: datetime

ProductUpdatePriceSchema:
└── price: Decimal

ProductApplyDiscountSchema:
└── discount_percentage: Decimal
```

**Future Evolution:**
- Add Field validators:
  - `name`: min_length=3, max_length=255
  - `price`: gt=0, le=10000000
  - `stock`: ge=0, le=1000000
  - `discount_percentage`: gt=0, lt=100
- Add `ProductListResponse` with pagination metadata
- Add `ProductDetailResponse` with images included

---

### app/schemas/product_image_schema.py

**Status:** ✅ Implemented

**Purpose:**
Pydantic models for product image operations.

**Current Schemas:**
```
ProductImageCreate:
└── image_url: HttpUrl

ProductImageResponse:
├── id: int
└── image_url: HttpUrl
```

**Future Evolution:**
- Add `position` field
- Add `alt_text` field
- Add URL domain validation (allowed CDN domains only)

---

### app/schemas/user_schema.py

**Status:** ✅ Implemented

**Purpose:**
Pydantic models for user operations.

**Current Schemas:**
```
UserCreate:
├── email: EmailStr
└── password: str

UserRead:
├── id: int
├── email: EmailStr
├── is_active: bool
└── created_at: datetime
```

**Future Evolution:**
- Add password validation:
  - min_length=8
  - require uppercase
  - require digit
  - require special character
- Add `UserUpdate` for profile changes
- Add `PasswordChange` schema
- Add `TokenResponse` for login response

---

### app/schemas/order_schema.py

**Status:** ✅ Implemented

**Purpose:**
Pydantic models for order operations.

**Current Schemas:**
```
OrderStatusSchema(Enum):
├── PENDING
├── PAID
└── FAILED

OrderCreate:
├── product_id: int
└── quantity: int

OrderRead:
├── id: int
├── product_id: int
├── quantity: int
├── total_amount: Decimal
├── status: OrderStatusSchema
└── created_at: datetime
```

**Future Evolution:**
- Add `idempotency_key` to OrderCreate
- Add `OrderListResponse` with pagination
- Add `OrderDetailResponse` with product details embedded
- Add quantity validation (ge=1, le=10)

---

## Security & Utilities

---

### security.py

**Status:** ✅ Implemented

**Purpose:**
Security utilities for password hashing and JWT token management.

**Responsibilities:**
- Hash passwords using bcrypt
- Verify password against hash
- Generate JWT access tokens
- Verify and decode JWT tokens

**What It Should NOT Do:**
- Store user data
- Handle HTTP requests
- Manage sessions

**Dependencies:**
- `passlib` — Password hashing
- `python-jose` — JWT encoding/decoding
- `app.core.config.settings` — Secret key, algorithm

**Current Implementation:**
```
pwd_context = CryptContext(schemes=["bcrypt"])

hash_password(password) → hashed string
verify_password(plain, hashed) → boolean
create_access_token(data) → JWT string
verify_access_token(token) → payload dict (raises on invalid)
```

**Future Evolution:**
- Add `create_refresh_token()` for token refresh flow
- Add token blacklist support for logout
- Add token type validation (access vs refresh)
- Add token version for forced invalidation
- Move to `app/core/security.py` for consistency

---

### app/core/dependencies.py

**Status:** ❌ Planned

**Purpose:**
FastAPI dependencies for authentication and authorization.

**Responsibilities:**
- Extract and validate JWT from request headers
- Resolve current user from token
- Check user roles/permissions
- Provide reusable auth dependencies

**What It Should NOT Do:**
- Hash passwords (security.py does this)
- Issue tokens (security.py does this)
- Contain business logic

**Dependencies:**
- `security.py` — Token verification
- `app.repositories.user_repo.UserRepository` — User lookup

**Planned Implementation:**
```
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

get_current_user(token, session) → User
    # Decode token, fetch user, validate active

get_current_active_user(user) → User
    # Verify user.is_active

require_admin(user) → User
    # Verify user.role == "admin"
```

---

### app/core/cache.py

**Status:** ❌ Planned

**Purpose:**
Redis cache integration for performance optimization.

**Responsibilities:**
- Provide Redis connection management
- Offer cache get/set/delete operations
- Handle serialization (JSON)
- Manage TTL for cache entries

**What It Should NOT Do:**
- Contain business logic
- Decide what to cache (callers decide)
- Handle cache invalidation strategy (callers decide)

**Dependencies:**
- `redis.asyncio` — Async Redis client
- `app.core.config.settings` — Redis URL

**Planned Implementation:**
```
redis_client = None  # Initialized on startup

async def get_redis() → Redis  # Dependency

async def cache_get(key) → Optional[str]
async def cache_set(key, value, ttl) → None
async def cache_delete(key) → None
async def cache_exists(key) → bool
```

---

### app/core/rate_limiter.py

**Status:** ❌ Planned

**Purpose:**
Rate limiting implementation to prevent abuse.

**Responsibilities:**
- Track request counts per user/IP
- Enforce rate limits
- Provide retry-after information
- Support different limits per endpoint

**What It Should NOT Do:**
- Block requests (raise exception, let router handle)
- Log violations (separate concern)

**Dependencies:**
- `app.core.cache.redis_client` — Redis for counters

**Planned Implementation:**
```
async def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int
) → tuple[bool, int]
    # Returns (allowed, retry_after_seconds)

# Usage as dependency:
async def rate_limit_purchase(user: User = Depends(get_current_user)):
    allowed, retry_after = await check_rate_limit(
        f"purchase:{user.id}", limit=10, window_seconds=60
    )
    if not allowed:
        raise HTTPException(429, headers={"Retry-After": str(retry_after)})
```

---

## Module Dependency Graph

```
Routers
   │
   ├── depends on → Schemas (request/response validation)
   ├── depends on → Services (business logic)
   └── depends on → Dependencies (auth, rate limiting)

Services
   │
   ├── depends on → Repositories (data access)
   ├── depends on → Other Services (orchestration)
   └── depends on → Security utilities

Repositories
   │
   ├── depends on → Models (ORM entities)
   └── depends on → Session (database connection)

Models
   │
   └── depends on → Base (declarative base)

Infrastructure (config, session, cache)
   │
   └── No domain dependencies (foundation layer)
```

**Rule:** Dependencies flow downward only. A lower layer never imports from a higher layer.

---

## Adding New Modules

When adding a new domain (e.g., "Promotions"):

1. **Model** (`app/models/promotion.py`)
   - Define table schema
   - Define relationships

2. **Schema** (`app/schemas/promotion_schema.py`)
   - Define request/response models
   - Add validators

3. **Repository** (`app/repositories/promotion_repo.py`)
   - Implement data access methods
   - No business logic

4. **Service** (`app/services/promotion_service.py`)
   - Implement business logic
   - Coordinate repository calls
   - Manage transactions

5. **Router** (`app/routers/promotions.py`)
   - Define endpoints
   - Wire up dependencies
   - Handle HTTP concerns

6. **Register** (`app/main.py`)
   - Import and mount router

7. **Test**
   - Unit tests for service (mock repository)
   - Integration tests for router (test client)

Follow existing patterns. When in doubt, look at product module as reference.
