# Flash Sale Engine — Architecture

> Technical architecture document explaining design decisions, data flow, and failure handling.

---

## Table of Contents

1. [Architectural Style](#architectural-style)
2. [Why This Architecture Fits Flash Sales](#why-this-architecture-fits-flash-sales)
3. [Data Flow Per Request](#data-flow-per-request)
4. [Concurrency Strategy](#concurrency-strategy)
5. [Failure Handling Philosophy](#failure-handling-philosophy)

---

## Architectural Style

### Layered Monolith with Repository Pattern

This system follows a **layered monolithic architecture** with clear separation of concerns. The layers, from top to bottom:

**Layer 1: Presentation (Routers)**
HTTP request handling. Receives requests, validates input via Pydantic schemas, calls appropriate service methods, and formats responses. Contains zero business logic. If you see an `if` statement checking business rules in a router, it's in the wrong place.

**Layer 2: Business Logic (Services)**
All business rules live here. Validation beyond schema (e.g., "discount cannot exceed 90%"), orchestration of multiple repository calls, transaction management, and domain-specific calculations. Services are the only layer that understands what a "flash sale" is.

**Layer 3: Data Access (Repositories)**
Pure database operations. Queries, inserts, updates, deletes. No business logic whatsoever. A repository method like `get_product_by_id` should work identically whether called during a flash sale or a normal day. Repositories return ORM objects, never raw dictionaries.

**Layer 4: Domain Models**
SQLAlchemy ORM classes that define database schema. Relationships, constraints, and column definitions. Models are passive data containers—they don't contain methods that perform business operations.

**Layer 5: Infrastructure**
Database connections, configuration management, external service clients (Redis, payment gateways). Shared utilities that any layer might need but that don't belong to a specific domain.

### Why Monolith Over Microservices

Flash sales have a unique constraint: **transactional integrity across stock and orders**. When a user purchases:

1. Stock must be decremented
2. Order must be created
3. These must succeed or fail together

In a microservices architecture, this requires distributed transactions (saga pattern, two-phase commit) which add latency and complexity. A monolith provides:

- Single database transaction spanning stock and order
- Simpler deployment and debugging
- Lower latency (no network hops between services)
- Easier to reason about failure modes

The tradeoff is horizontal scaling complexity, but for a startup handling up to 100k concurrent users, a well-optimized monolith with read replicas is sufficient. Microservices become worthwhile when team size exceeds 50+ engineers or when different domains have fundamentally different scaling needs.

### Repository Pattern Justification

Repositories abstract database access behind an interface. This provides:

**Testability**: Services can be tested with mock repositories. No database required for unit tests.

**Query Centralization**: All queries for a domain live in one place. Need to add an index? Check the repository to see all query patterns.

**Database Agnosticism**: Though rarely used in practice, switching databases or adding caching layers becomes possible without touching service code.

**Single Responsibility**: Services focus on "what" (business rules), repositories focus on "how" (query construction).

---

## Why This Architecture Fits Flash Sales

### Problem Characteristics

Flash sales have specific technical challenges:

**Extreme Read/Write Ratio Imbalance**: Product listing pages are read 10,000 times for every 1 purchase. This suggests aggressive caching for reads, careful optimization for writes.

**Hot Spot Data**: A single product (the flash sale item) receives orders of magnitude more traffic than everything else combined. Unlike normal e-commerce where traffic spreads across catalog.

**Time-Bounded Load**: Traffic spikes at sale start time, sustains for minutes, then drops. The system must handle peak load, not average load.

**Zero Tolerance for Inconsistency**: Overselling costs real money. Unlike a social media feed where stale data is acceptable, inventory must be accurate to the unit.

### How the Architecture Addresses These

**Layered Separation Enables Targeted Optimization**

Read-heavy operations (product listings) flow through repositories that can be backed by cache. Write-heavy operations (order placement) flow through services that implement locking. The architecture allows different strategies per use case without coupling.

**Service Layer as Transaction Boundary**

The service layer owns transaction demarcation. A service method like `place_order()` begins a transaction, performs all operations (lock stock, decrement, create order), and commits atomically. Routers never start transactions. Repositories never commit. This centralization prevents partial writes.

**Repository Pattern Enables Lock Encapsulation**

The repository method `get_product_for_update()` encapsulates the `SELECT ... FOR UPDATE` pattern. Services call this method without knowing SQL details. If we later switch to Redis-based distributed locks, only the repository changes.

**Monolith Simplifies Atomic Operations**

Stock decrement and order creation happen in the same process, same database connection, same transaction. No network partition can split them. No eventual consistency delay. Either both happen or neither happens.

### What This Architecture Cannot Do

**Unlimited Horizontal Scaling**: A monolith scales vertically (bigger server) more easily than horizontally (more servers). Beyond a certain point, we'd need to shard the database or extract hot-path services.

**Independent Deployment**: All code deploys together. A bug in product images affects order placement deployment.

**Polyglot Persistence**: All domains use the same database. If orders needed a different storage engine than products, the monolith makes that awkward.

These limitations are acceptable for the current scale. The architecture can evolve.

---

## Data Flow Per Request

### Read Flow: Get Product List

```
1. HTTP Request arrives at FastAPI
   - Method: GET
   - Path: /products
   - Headers: Authorization (optional for public listings)

2. Router receives request
   - FastAPI dependency injection provides database session
   - Router instantiates ProductService with session
   - Router calls service.get_products(page, limit, search)

3. Service applies business logic
   - Validates pagination parameters (page >= 1, limit <= 50)
   - Decides whether to filter by active status
   - Calls repository with cleaned parameters

4. Repository executes query
   - Constructs SQLAlchemy SELECT statement
   - Applies WHERE, ORDER BY, OFFSET, LIMIT
   - Executes against database
   - Returns list of Product ORM objects

5. Service returns results
   - No transformation needed for read operations
   - Returns ORM objects directly

6. Router formats response
   - Pydantic schema serializes ORM objects to JSON
   - FastAPI sends HTTP 200 with JSON body

Database Interaction: 1 SELECT query
Transaction: Read-only, auto-commit
Caching Opportunity: High (add Redis layer at repository)
```

### Write Flow: Place Order (Future Implementation)

```
1. HTTP Request arrives at FastAPI
   - Method: POST
   - Path: /orders
   - Headers: Authorization (required)
   - Body: { "product_id": 123, "quantity": 1 }

2. Router receives request
   - FastAPI validates body against OrderCreate schema
   - Dependency injection provides: database session, current user
   - Router instantiates OrderService with session
   - Router calls service.place_order(user_id, product_id, quantity)

3. Service begins transaction
   - Implicit transaction start on first query
   - All subsequent operations are part of same transaction

4. Service acquires inventory lock
   - Calls repository.get_product_for_update(product_id)
   - Repository executes: SELECT ... FOR UPDATE
   - Row is now locked; other transactions wait

5. Service validates business rules
   - Is product active?
   - Is stock >= quantity?
   - Has user exceeded purchase limit?
   - If any fail: raise exception (triggers rollback)

6. Service decrements stock
   - Modifies ORM object: product.stock -= quantity
   - Change tracked by SQLAlchemy, not yet written

7. Service creates order
   - Constructs Order ORM object
   - Calls repository.create(order)
   - Repository executes: INSERT INTO orders

8. Service commits transaction
   - Calls session.commit()
   - Both UPDATE (stock) and INSERT (order) execute atomically
   - Row lock released

9. Router formats response
   - Returns order details with status PENDING
   - HTTP 201 Created

Database Interaction: 1 SELECT FOR UPDATE, 1 UPDATE, 1 INSERT
Transaction: Read-write, explicit commit
Lock Duration: From step 4 to step 8 (~50-200ms ideally)
Failure at any step: Automatic rollback, stock unchanged
```

### Webhook Flow: Payment Confirmation

```
1. HTTP Request arrives from payment gateway
   - Method: POST
   - Path: /webhooks/razorpay
   - Headers: X-Razorpay-Signature
   - Body: { "order_id": "...", "status": "SUCCESS", ... }

2. Router receives request
   - Verifies signature using gateway's public key
   - If signature invalid: return 401, log security event
   - If valid: proceed

3. Service processes payment confirmation
   - Looks up order by payment reference
   - Checks idempotency: already processed?
   - If already processed: return 200 (acknowledge, no action)

4. Service updates order status
   - order.status = PAID
   - Commit transaction

5. Service triggers downstream actions (async)
   - Queue email confirmation task
   - Queue inventory sync task
   - These run in background workers, not blocking webhook

6. Router returns acknowledgment
   - HTTP 200 (tells gateway to stop retrying)
   - Body content doesn't matter to gateway

Critical Requirement: Handler must be idempotent
Critical Requirement: Handler must return 200 even if downstream fails
Critical Requirement: Handler must complete within gateway timeout (~30s)
```

---

## Concurrency Strategy

### The Core Problem

Flash sale concurrency is not about handling many requests. It's about handling many requests **for the same resource**. A system might handle 100k requests/second easily if they're for different products. But 100k requests/second for the same 100 iPhones is a different problem entirely.

### Strategy 1: Pessimistic Locking at Database Level

For stock operations, we use `SELECT ... FOR UPDATE`. This is a database-level exclusive lock on specific rows.

**How it works**: When a transaction executes `SELECT * FROM products WHERE id = 1 FOR UPDATE`, the database:
1. Acquires an exclusive lock on row with id=1
2. Blocks any other transaction trying to read-for-update or update that row
3. Holds lock until transaction commits or rolls back

**Why this works for flash sales**: The database serializes access to hot-spot rows. Even if 1000 requests arrive simultaneously, they process one-by-one through the lock.

**Tradeoff**: Lock contention creates queuing. If each transaction holds the lock for 100ms, throughput is capped at 10 transactions/second per product. Mitigation: minimize lock duration by doing only essential work while holding lock.

### Strategy 2: Atomic Decrement Pattern

An alternative to lock-then-update is atomic decrement:

```sql
UPDATE products 
SET stock = stock - 1 
WHERE id = 1 AND stock >= 1
RETURNING stock
```

**How it works**: The database evaluates `stock >= 1` and performs the decrement atomically. No explicit lock needed. If `stock < 1`, zero rows affected.

**Why this works**: The WHERE clause and UPDATE happen as single atomic operation. No window for race condition.

**Tradeoff**: Doesn't allow complex validation before decrement. If you need to check "user hasn't exceeded limit" before decrementing, you're back to pessimistic locking.

### Strategy 3: Application-Level Rate Limiting

Before requests even reach the database, rate limiting reduces load:

**Per-user limit**: 10 purchase attempts per minute. Prevents single user from consuming all capacity.

**Per-product limit**: 1000 concurrent requests allowed. Excess requests receive 503 immediately instead of waiting.

**Global limit**: System-wide requests-per-second cap. Protects database from overload.

**Implementation**: Redis-based counters with sliding window algorithm. Fast (sub-millisecond) rejection of excess requests.

### Strategy 4: Queue-Based Serialization (Phase 4)

For extreme scale, requests don't hit the database directly. Instead:

1. Request adds to Redis queue: `LPUSH order_queue {...}`
2. Response immediately: "Your order is queued, position #847"
3. Background workers process queue sequentially
4. User polls or receives WebSocket notification when processed

**Why this works**: Queue is append-only, infinitely fast. Database processes at sustainable rate. Users get instant feedback even if final result takes seconds.

**Tradeoff**: Complexity. User experience requires position tracking, notifications, timeout handling.

### Concurrency by Component

| Component | Concurrency Approach | Rationale |
|-----------|---------------------|-----------|
| Product reads | No locking, cached | Read-only, stale data acceptable |
| Stock check | Pessimistic lock | Must be accurate, high contention |
| Order creation | Within stock lock | Atomic with stock decrement |
| Payment processing | Async, idempotent | External dependency, unreliable |
| Stock restoration | Pessimistic lock | Must not over-restore |

---

## Failure Handling Philosophy

### Principle 1: Fail Fast, Fail Loud

When something cannot succeed, reject immediately with clear error. Do not:
- Retry silently and succeed partially
- Return 200 with error in body
- Hang waiting for timeout

Example: Stock unavailable? Return 409 Conflict immediately. Don't wait, don't retry, don't queue for later.

### Principle 2: Transactions Are Sacred

A transaction represents a unit of business logic that must fully complete or fully abort. There is no middle ground.

**Commit only at the end**: All operations in a service method share one transaction. Commit happens once, at the end, after all validations pass.

**Rollback on any failure**: If any step fails, rollback reverts all changes. The database returns to its pre-transaction state.

**Never catch-and-continue**: If `decrement_stock()` fails, don't catch the exception and proceed to `create_order()`. Let it bubble up.

### Principle 3: Idempotency for External Interactions

External systems (payment gateways, email services, webhooks) are unreliable. They may:
- Timeout and retry
- Succeed but not acknowledge
- Send duplicate callbacks

Every external-facing endpoint must be idempotent. Processing the same request twice must produce the same result, not double the effect.

**Implementation**: Store unique request identifiers. Before processing, check if already processed. If yes, return cached result.

### Principle 4: Compensating Actions Over Distributed Transactions

When an operation spans multiple systems (our database + payment gateway), we cannot have atomic transactions. Instead:

**Optimistic approach**: 
1. Reserve stock locally (can rollback)
2. Charge payment externally (cannot rollback)
3. If payment succeeds: finalize stock
4. If payment fails: release stock

**Compensation on failure**:
1. If payment times out: mark order as PENDING, schedule retry
2. If payment confirmed failed: release stock, mark order FAILED
3. If payment confirmed success after timeout: check order status, finalize if still pending

**Never assume**: Don't assume payment failed because of timeout. It might have succeeded. Always verify with gateway before compensating.

### Principle 5: Graceful Degradation Over Total Failure

When a component fails, the system should continue serving requests that don't depend on that component.

**Cache fails**: Fall back to database. Slower, but working.

**Payment gateway fails**: Allow order creation with PENDING status. Process payment when gateway recovers.

**Database read replica fails**: Route reads to primary. Higher load, but working.

**Background worker fails**: Critical path (order creation) still works. Non-critical tasks (emails) queue up for later.

### Failure Response Matrix

| Failure Scenario | User Impact | System Response |
|-----------------|-------------|-----------------|
| Invalid input | Immediate 400 error | Clear error message, no retry |
| Out of stock | Immediate 409 error | Clear message, suggest alternatives |
| Database timeout | 503 error | Log, alert, user can retry |
| Payment gateway down | Order created as PENDING | Retry payment async, notify user |
| Redis down | Degraded performance | Fall back to DB, disable rate limiting |
| Webhook signature invalid | Reject silently | Log security event, alert |
| Duplicate webhook | Acknowledge, no action | Return 200, idempotency key match |

### Error Response Contract

All errors return consistent structure:

```json
{
  "detail": "Human-readable message",
  "code": "MACHINE_READABLE_CODE",
  "retry_after": 5
}
```

**detail**: For display to end users (localized if needed).

**code**: For client-side logic (e.g., `OUT_OF_STOCK`, `RATE_LIMITED`, `PAYMENT_FAILED`).

**retry_after**: Seconds before retrying makes sense. Null if retry won't help.

---

## Summary

This architecture is designed for a specific problem: high-concurrency sales of limited inventory. Every decision—from monolith over microservices, to pessimistic locking, to fail-fast philosophy—serves that goal.

The architecture is intentionally simple. Complexity can be added incrementally:
- Phase 2 adds Redis caching and rate limiting
- Phase 3 adds idempotency and comprehensive failure handling
- Phase 4 adds distributed locking and queue-based processing

Each addition addresses a specific scaling bottleneck. We don't add complexity until the simpler solution is proven insufficient.

For implementation details on specific components, see the deep dive documents in `planning/deep_dives/`.
