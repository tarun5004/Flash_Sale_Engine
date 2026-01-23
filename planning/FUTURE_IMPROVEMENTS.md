# Flash Sale Engine — Future Improvements

> A senior backend architect's guide to building a production-grade flash sale system.
> Each improvement is analyzed for: purpose, implementation approach, risks, and timing.

---

## Table of Contents

1. [Authentication & Authorization](#1-authentication--authorization)
2. [Stock Reservation & Locking](#2-stock-reservation--locking)
3. [Idempotency System](#3-idempotency-system)
4. [Redis Caching Layer](#4-redis-caching-layer)
5. [Rate Limiting](#5-rate-limiting)
6. [Background Job Processing](#6-background-job-processing)
7. [Payment Integration](#7-payment-integration)
8. [Database Optimization](#8-database-optimization)
9. [Distributed Locking](#9-distributed-locking)
10. [Queue-Based Order Processing](#10-queue-based-order-processing)
11. [Circuit Breakers](#11-circuit-breakers)
12. [Observability & Monitoring](#12-observability--monitoring)
13. [Audit Logging & Event Sourcing](#13-audit-logging--event-sourcing)
14. [Graceful Degradation](#14-graceful-degradation)

---

## 1. Authentication & Authorization

### What It Is
JWT-based authentication system with role-based access control (RBAC). Users authenticate once, receive a token, and include it in subsequent requests.

### Why It Is Needed
- Currently ALL endpoints are public — anyone can create products, change prices, manipulate stock
- Flash sale with real money = users must be identified
- Admin operations (price change, stock update) must be restricted
- Order history must be tied to authenticated users

### High-Level Implementation
```
Components:
├── /auth/register — Create user account
├── /auth/login — Return JWT token
├── get_current_user() — FastAPI dependency that validates token
├── require_admin() — Dependency that checks user.role == "admin"
└── User.role field — "customer" | "admin"

Flow:
1. User calls /auth/login with email + password
2. Server validates credentials, returns JWT
3. Client includes "Authorization: Bearer <token>" in requests
4. get_current_user() extracts user from token
5. Protected endpoints use Depends(get_current_user)
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Storing JWT in localStorage | XSS attack can steal tokens |
| No token expiry | Stolen token works forever |
| Checking role in frontend only | Backend still allows admin operations |
| Using user ID from request body | User can impersonate others |
| Weak SECRET_KEY | Tokens can be forged |

### When to Implement
**Phase 1 (MVP)** — Cannot have orders without knowing who placed them.

---

## 2. Stock Reservation & Locking

### What It Is
Mechanism to atomically check and decrement stock during purchase, preventing overselling even under extreme concurrency.

### Why It Is Needed
Without locking, this happens:
```
Stock = 1

User A: SELECT stock → sees 1
User B: SELECT stock → sees 1  (same moment)
User A: UPDATE stock = 0 ✅
User B: UPDATE stock = -1 ❌ OVERSOLD
```

Flash sale = thousands of users clicking "Buy" simultaneously on limited stock.

### High-Level Implementation
```
Approach 1: Database Row Lock (FOR UPDATE)
─────────────────────────────────────────
BEGIN TRANSACTION
  SELECT * FROM products WHERE id=1 FOR UPDATE  ← Lock row
  IF stock >= quantity:
      UPDATE stock = stock - quantity
      INSERT INTO orders (...)
  ELSE:
      RAISE "Out of stock"
COMMIT  ← Release lock

Approach 2: Atomic Decrement (Optimistic)
─────────────────────────────────────────
UPDATE products 
SET stock = stock - 1 
WHERE id = 1 AND stock >= 1
RETURNING stock

IF rows_affected == 0:
    RAISE "Out of stock"
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Lock held too long | Other users timeout waiting |
| Forgetting COMMIT | Locks never release, deadlock |
| Check-then-update (two queries) | Race condition between check and update |
| Locking entire table | All products blocked, not just one |
| No timeout on lock acquisition | Infinite wait under load |

### When to Implement
**Phase 1 (MVP)** — Flash sale without this is not a flash sale, it's a disaster.

---

## 3. Idempotency System

### What It Is
Guarantee that repeating the same request produces the same result without side effects. Essential for payments and order creation.

### Why It Is Needed
Network is unreliable:
```
User clicks "Pay" → Request sent → Network timeout → User sees error
But payment actually succeeded on server!
User clicks "Pay" again → DOUBLE CHARGE 💸
```

Idempotency ensures: same request twice = same order, not two orders.

### High-Level Implementation
```
Database:
  orders.idempotency_key = UNIQUE VARCHAR(64)

Flow:
1. Client generates idempotency_key (UUID) before request
2. Client sends: POST /orders {idempotency_key: "abc-123", ...}
3. Server checks: SELECT * FROM orders WHERE idempotency_key = "abc-123"
4. If exists → return existing order (no new creation)
5. If not → create order with this key

Key Generation Rules:
- Client generates, not server
- Unique per user + action (e.g., user_id + product_id + timestamp)
- Stored forever (or at least 24-48 hours)
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Server generates key | Client retries create duplicates anyway |
| Key expires too fast | Retry after 1 hour creates duplicate |
| Key not indexed | Slow lookups under load |
| Key per user only | Same user, different products = conflict |
| No key for webhooks | Payment gateway retries = chaos |

### When to Implement
**Phase 3 (Production-Hardening)** — MVP can survive without it for testing, but required before real money.

---

## 4. Redis Caching Layer

### What It Is
In-memory cache sitting between application and database. Serves frequently-read data without hitting DB.

### Why It Is Needed
Flash sale homepage load:
```
Without cache:
  100,000 users → 100,000 DB queries → DB dies

With cache:
  100,000 users → 1 DB query + 99,999 cache hits → DB survives
```

### High-Level Implementation
```
Cache Strategy: Cache-Aside (Lazy Loading)
──────────────────────────────────────────
async def get_product(product_id):
    # 1. Check cache first
    cached = await redis.get(f"product:{product_id}")
    if cached:
        return json.loads(cached)
    
    # 2. Cache miss → hit DB
    product = await db.get_product(product_id)
    
    # 3. Store in cache for next time
    await redis.setex(
        f"product:{product_id}",
        ttl=300,  # 5 minutes
        json.dumps(product)
    )
    return product

Cache Invalidation:
──────────────────
async def update_product(product_id, data):
    await db.update_product(product_id, data)
    await redis.delete(f"product:{product_id}")  # Invalidate

What to Cache:
- Product listings (high read, low write)
- Product details (high read)
- User sessions (auth tokens)

What NOT to Cache:
- Stock counts (changes every purchase)
- Order status (changes frequently)
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Caching stock count | Users see wrong availability |
| No TTL on cache | Stale data forever |
| Cache invalidation missed | DB updated but cache shows old data |
| Thundering herd | Cache expires, 100k requests hit DB simultaneously |
| JSON serialization errors | Cache corrupted, app crashes |

### When to Implement
**Phase 2 (Scale-Ready)** — MVP works without cache. At 100+ users, DB becomes bottleneck.

---

## 5. Rate Limiting

### What It Is
Restrict how many requests a user/IP can make in a time window. Prevents abuse and protects resources.

### Why It Is Needed
Without rate limiting:
```
Bot sends 10,000 requests/second to /orders
→ Exhausts DB connections
→ Legitimate users get timeouts
→ Flash sale fails
```

Also prevents:
- Brute force login attacks
- Inventory scraping
- Price manipulation attempts

### High-Level Implementation
```
Algorithm: Sliding Window (Redis-based)
───────────────────────────────────────
async def check_rate_limit(user_id: str, limit: int = 10, window: int = 60):
    key = f"rate:{user_id}"
    current = await redis.incr(key)
    
    if current == 1:
        await redis.expire(key, window)  # First request, set TTL
    
    if current > limit:
        raise HTTPException(429, "Too many requests")

Limits by Endpoint:
───────────────────
| Endpoint | Limit | Window | Reason |
|----------|-------|--------|--------|
| /auth/login | 5 | 60s | Prevent brute force |
| /orders | 10 | 60s | Prevent bot purchases |
| /products | 100 | 60s | Allow browsing |
| /products (search) | 30 | 60s | Expensive query |
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Rate limit by IP only | Shared IP (office) = everyone blocked |
| Same limit for all endpoints | Either too strict or too loose |
| No bypass for admin | Admin locked out during incident |
| Limit too high | Doesn't actually protect |
| No 429 response headers | Client doesn't know when to retry |

### When to Implement
**Phase 2 (Scale-Ready)** — Essential before any public launch with real traffic.

---

## 6. Background Job Processing

### What It Is
Offload slow/heavy tasks to separate worker processes. Request returns immediately, work happens async.

### Why It Is Needed
Some operations are slow:
```
Synchronous (bad):
  User clicks "Pay" → Wait 5s for payment gateway → Response

Asynchronous (good):
  User clicks "Pay" → Order created (PENDING) → Response in 100ms
  Background: Process payment → Update order to PAID → Send email
```

Flash sale context: You can't make 100k users wait 5 seconds each.

### High-Level Implementation
```
Architecture:
─────────────
┌─────────┐    ┌─────────┐    ┌─────────┐
│ FastAPI │───▶│  Redis  │◀───│ Celery  │
│   API   │    │ (Queue) │    │ Worker  │
└─────────┘    └─────────┘    └─────────┘
                                   │
                              ┌────▼────┐
                              │ Payment │
                              │ Gateway │
                              └─────────┘

Task Examples:
─────────────
@celery.task
def process_payment(order_id: int):
    order = get_order(order_id)
    result = payment_gateway.charge(order.amount)
    
    if result.success:
        update_order_status(order_id, "PAID")
        send_confirmation_email(order.user_email)
    else:
        update_order_status(order_id, "FAILED")
        restore_stock(order.product_id, order.quantity)

# In API endpoint:
@router.post("/orders")
async def create_order(...):
    order = await order_service.create(...)  # Quick DB insert
    process_payment.delay(order.id)  # Queue for background
    return {"order_id": order.id, "status": "PENDING"}
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| No retry on failure | Failed payment = stuck order forever |
| No dead letter queue | Failed tasks disappear silently |
| Worker crashes mid-task | Inconsistent state (payment done, DB not updated) |
| Too many retries | User charged 10 times |
| No task timeout | Stuck task blocks worker |

### When to Implement
**Phase 2 (Scale-Ready)** — MVP can be synchronous for testing. Required before real traffic.

---

## 7. Payment Integration

### What It Is
Integration with payment gateways (Razorpay, Stripe, PayU) to collect money from users.

### Why It Is Needed
Flash sale without payment = giving products for free.

### High-Level Implementation
```
Flow (Redirect-based):
─────────────────────
1. User clicks "Pay" 
2. Server creates order (PENDING), generates payment session
3. Redirect user to payment gateway page
4. User enters card details on gateway (not our server!)
5. Gateway processes payment
6. Gateway redirects user back to our callback URL
7. Gateway sends webhook to confirm payment
8. We update order to PAID

Architecture:
────────────
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│  Server  │────▶│ Razorpay │
└──────────┘     └──────────┘     └──────────┘
     │                 │                │
     │    redirect     │    webhook     │
     ◀─────────────────┼────────────────│
                       │                │
                       ◀────────────────┘

Webhook Handling:
────────────────
POST /webhooks/razorpay
1. Verify signature (CRITICAL — ensures request is from gateway)
2. Find order by payment_id
3. Check idempotency (already processed?)
4. Update order status
5. Return 200 (gateway will retry if not 200)
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| No signature verification | Attacker fakes "payment success" |
| Trusting redirect over webhook | User can manipulate redirect URL |
| No idempotency on webhook | Gateway retries = double fulfillment |
| Storing card details | PCI compliance violation, massive liability |
| Blocking webhook handler | Gateway times out, keeps retrying |
| No reconciliation | Money received but order stuck |

### When to Implement
**Phase 1 (MVP)** — Can't launch without it. Use test mode initially.

---

## 8. Database Optimization

### What It Is
Indexes, query optimization, connection pooling, and read replicas to handle scale.

### Why It Is Needed
```
Without indexes:
  SELECT * FROM products WHERE name ILIKE '%phone%'
  → Full table scan → 5 seconds with 1M products

With index:
  → Index lookup → 5 milliseconds
```

Flash sale = every millisecond counts.

### High-Level Implementation
```
Essential Indexes:
─────────────────
-- Products
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_active_name ON products(is_active, name);

-- Orders
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at);
CREATE UNIQUE INDEX idx_orders_idempotency ON orders(idempotency_key);

-- Users
CREATE UNIQUE INDEX idx_users_email ON users(email);

Connection Pooling:
──────────────────
# SQLAlchemy config
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Base connections
    max_overflow=30,        # Extra during spike
    pool_timeout=30,        # Wait time for connection
    pool_recycle=1800,      # Recycle stale connections
)

Read Replicas (Phase 4):
───────────────────────
write_engine = create_engine(PRIMARY_DB_URL)
read_engine = create_engine(REPLICA_DB_URL)

# Write operations → primary
# Read operations → replica
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Index on every column | Slow writes, wasted storage |
| No composite indexes | Query still slow |
| Pool too small | Connections exhausted under load |
| Pool too large | Database overwhelmed |
| Replica lag not handled | User sees stale data after write |

### When to Implement
**Phase 2 (Scale-Ready)** — Indexes and pooling. **Phase 4** — Read replicas.

---

## 9. Distributed Locking

### What It Is
Locks that work across multiple server instances. Essential when running more than one app server.

### Why It Is Needed
Single server:
```
Server A: FOR UPDATE locks row → works ✅
```

Multiple servers:
```
Server A: FOR UPDATE locks row
Server B: FOR UPDATE locks row (different DB connection!)
→ Both get lock → Both decrement → OVERSOLD ❌
```

Database locks are per-connection. Distributed lock is application-level.

### High-Level Implementation
```
Redis-based Lock (Redlock pattern simplified):
─────────────────────────────────────────────
async def acquire_lock(resource: str, ttl: int = 10) -> bool:
    lock_key = f"lock:{resource}"
    lock_value = str(uuid.uuid4())  # Unique per acquisition
    
    acquired = await redis.set(
        lock_key, 
        lock_value,
        nx=True,      # Only if not exists
        ex=ttl        # Auto-expire
    )
    
    if acquired:
        return lock_value  # Return value to release later
    return None

async def release_lock(resource: str, lock_value: str):
    lock_key = f"lock:{resource}"
    # Only delete if we own the lock
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    await redis.eval(script, [lock_key], [lock_value])

Usage:
─────
lock = await acquire_lock(f"purchase:{product_id}")
if not lock:
    raise HTTPException(429, "Try again")
try:
    await process_purchase(...)
finally:
    await release_lock(f"purchase:{product_id}", lock)
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| No TTL on lock | Lock held forever if server crashes |
| Releasing wrong lock | Another process's lock released |
| Lock scope too broad | One product locks all products |
| Lock scope too narrow | Race condition still possible |
| Redis single point of failure | Redis down = no locks = chaos |

### When to Implement
**Phase 4 (Enterprise)** — Only needed with multiple server instances.

---

## 10. Queue-Based Order Processing

### What It Is
Instead of processing orders synchronously, put them in a queue. Process in order, handle backpressure.

### Why It Is Needed
```
Flash sale starts, 100k users click "Buy" in 1 second:

Synchronous:
  → 100k concurrent DB transactions
  → Database explodes
  → Everyone gets timeout

Queue-based:
  → 100k requests add to queue (fast, just Redis LPUSH)
  → Workers process 1000/second
  → Users get "Order #12345, position 847 in queue"
  → Everyone eventually gets processed
```

### High-Level Implementation
```
Architecture:
────────────
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌────────┐
│ Client  │────▶│   API   │────▶│  Queue  │────▶│ Worker │
└─────────┘     └─────────┘     └─────────┘     └────────┘
     │                                               │
     │         WebSocket / Polling                   │
     ◀───────────────────────────────────────────────┘
                 "Your order is confirmed!"

API Endpoint:
────────────
@router.post("/orders/enqueue")
async def enqueue_order(payload: OrderCreate, user: User):
    # Quick validation only
    if not await has_stock(payload.product_id):
        raise HTTPException(400, "Out of stock")
    
    # Add to queue, return immediately
    ticket_id = str(uuid.uuid4())
    await redis.lpush("order_queue", json.dumps({
        "ticket_id": ticket_id,
        "user_id": user.id,
        "product_id": payload.product_id,
        "quantity": payload.quantity,
    }))
    
    return {"ticket_id": ticket_id, "status": "QUEUED"}

Worker:
──────
while True:
    item = await redis.brpop("order_queue")
    data = json.loads(item)
    
    try:
        order = await create_order_atomically(data)
        await notify_user(data["ticket_id"], "SUCCESS", order.id)
    except OutOfStockError:
        await notify_user(data["ticket_id"], "SOLD_OUT")
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Queue unbounded | Memory exhaustion |
| No position feedback | Users keep refreshing, more load |
| Worker too slow | Queue grows faster than processed |
| No dead letter queue | Failed orders lost |
| FIFO not guaranteed | Early users served later |

### When to Implement
**Phase 4 (Enterprise)** — Overkill for MVP. Essential at 10k+ concurrent users.

---

## 11. Circuit Breakers

### What It Is
Automatically stop calling a failing service. Prevent cascade failures.

### Why It Is Needed
```
Payment gateway goes down:

Without circuit breaker:
  → Every request waits 30s for timeout
  → Thread pool exhausted
  → Entire app becomes unresponsive
  → Users can't even browse products

With circuit breaker:
  → After 5 failures, circuit "opens"
  → Subsequent requests fail immediately (no wait)
  → App stays responsive for other features
  → Circuit "closes" after gateway recovers
```

### High-Level Implementation
```
States:
──────
CLOSED (normal) → failures < threshold → allow requests
OPEN (tripped) → failures >= threshold → reject immediately
HALF-OPEN (testing) → after cooldown → allow one request to test

Implementation:
──────────────
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=30):
        self.failures = 0
        self.threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = "CLOSED"
        self.last_failure_time = None
    
    async def call(self, func, *args):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF-OPEN"
            else:
                raise CircuitOpenError("Service unavailable")
        
        try:
            result = await func(*args)
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.threshold:
                self.state = "OPEN"
            raise

Usage:
─────
payment_breaker = CircuitBreaker(failure_threshold=5)

async def charge_payment(order):
    return await payment_breaker.call(
        payment_gateway.charge, 
        order.amount
    )
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Threshold too low | Circuit opens on transient errors |
| Threshold too high | Too many failures before protection |
| Reset timeout too short | Circuit flaps open/closed |
| No fallback | User sees ugly error |
| Shared circuit for unrelated services | One failure affects all |

### When to Implement
**Phase 4 (Enterprise)** — Nice-to-have for resilience. Required for production SLAs.

---

## 12. Observability & Monitoring

### What It Is
Metrics, logs, and traces that let you understand what's happening in production.

### Why It Is Needed
Flash sale crashes at midnight:
```
Without observability:
  "Something is slow. Maybe database? Maybe Redis? No idea."
  → Hours of guessing

With observability:
  Dashboard shows:
  - Database latency: 2ms ✅
  - Redis latency: 1ms ✅  
  - Payment gateway latency: 15 seconds ❌
  → Found in 30 seconds
```

### High-Level Implementation
```
Three Pillars:
─────────────

1. METRICS (Prometheus + Grafana)
   - Request rate (requests/second)
   - Error rate (5xx/total)
   - Latency percentiles (p50, p95, p99)
   - Queue depth
   - DB connection pool usage

2. LOGS (Structured JSON)
   {
     "timestamp": "2026-01-24T10:00:00Z",
     "level": "ERROR",
     "request_id": "abc-123",
     "user_id": 456,
     "action": "create_order",
     "error": "Payment timeout",
     "duration_ms": 30000
   }

3. TRACES (OpenTelemetry)
   Request → API (50ms) → Service (20ms) → DB (5ms)
                       → Redis (2ms)
                       → Payment (25000ms) ← bottleneck!

Key Dashboards:
──────────────
- Flash Sale Overview: Orders/min, revenue, stock remaining
- System Health: CPU, memory, DB connections
- Error Tracking: Error rate by endpoint, stack traces
- Payment: Success rate, average processing time
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Logging PII (passwords, cards) | Security/compliance violation |
| Too many metrics | Expensive storage, slow dashboards |
| No alerting | Issues discovered by users |
| Alert fatigue | Real alerts ignored |
| No request IDs | Can't trace single request across services |

### When to Implement
**Phase 4 (Enterprise)** — Basic logging in Phase 1. Full observability for SLA requirements.

---

## 13. Audit Logging & Event Sourcing

### What It Is
Immutable log of every state change. Who did what, when, and what was the before/after.

### Why It Is Needed
```
Dispute: "I was charged ₹999 but product was ₹499!"

Without audit log:
  → No proof either way
  → Customer angry, you lose money

With audit log:
  Event: price_changed
  Before: 499
  After: 999
  By: admin@company.com
  At: 2026-01-24 09:00:00 (before purchase at 10:00:00)
  → Clear evidence for dispute resolution
```

Also required for: PCI compliance, GDPR, financial audits.

### High-Level Implementation
```
Audit Log Table:
───────────────
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(50),      -- 'product', 'order', 'user'
    entity_id INTEGER,
    action VARCHAR(50),           -- 'created', 'updated', 'deleted'
    actor_id INTEGER,             -- Who did it
    actor_type VARCHAR(20),       -- 'user', 'admin', 'system'
    old_values JSONB,             -- State before
    new_values JSONB,             -- State after
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for lookups
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_time ON audit_logs(created_at);

Implementation:
──────────────
async def update_price(product_id: int, new_price: Decimal, actor: User):
    product = await get_product(product_id)
    old_price = product.price
    
    product.price = new_price
    await db.commit()
    
    # Audit log (never skip, never fail silently)
    await create_audit_log(
        entity_type="product",
        entity_id=product_id,
        action="price_updated",
        actor_id=actor.id,
        old_values={"price": str(old_price)},
        new_values={"price": str(new_price)},
    )
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Mutable audit logs | Logs can be tampered |
| Audit log in same transaction | Failed transaction = lost audit |
| Missing actor info | "Someone" changed price |
| Logging too little | Not enough detail for investigation |
| Logging too much | Performance impact, storage costs |

### When to Implement
**Phase 3 (Production-Hardening)** — Required before handling real money and disputes.

---

## 14. Graceful Degradation

### What It Is
When parts of system fail, continue serving users with reduced functionality instead of complete failure.

### Why It Is Needed
```
Redis goes down during flash sale:

Without graceful degradation:
  → Cache miss → Exception → 500 error
  → Flash sale completely dead

With graceful degradation:
  → Cache miss → Log warning → Fall back to DB
  → Slower, but working
  → Flash sale continues
```

### High-Level Implementation
```
Pattern: Fallback Chain
──────────────────────
async def get_product(product_id: int):
    # Try cache first
    try:
        cached = await redis.get(f"product:{product_id}")
        if cached:
            return json.loads(cached)
    except RedisError:
        logger.warning("Redis unavailable, falling back to DB")
    
    # Fallback to database
    return await db.get_product(product_id)

Pattern: Feature Flags
─────────────────────
async def place_order(payload: OrderCreate):
    # If payment gateway down, allow "Cash on Delivery" only
    if not await is_payment_gateway_healthy():
        if payload.payment_method != "COD":
            raise HTTPException(
                503, 
                "Online payments temporarily unavailable. Use Cash on Delivery."
            )
    
    return await create_order(payload)

Pattern: Static Fallback
───────────────────────
async def get_products():
    try:
        return await db.get_active_products()
    except DatabaseError:
        # Serve stale data from file (last known good state)
        return load_products_from_static_file()
```

### What Can Go Wrong
| Mistake | Consequence |
|---------|-------------|
| Fallback also fails | User sees error anyway |
| Degraded mode too generous | Stock oversold, money lost |
| No monitoring of degraded state | Don't know system is degraded |
| Fallback becomes primary | Original issue never fixed |
| Silent degradation | Users get bad experience unknowingly |

### When to Implement
**Phase 4 (Enterprise)** — Requires mature error handling and monitoring first.

---

## Summary Matrix

| Improvement | Phase | Complexity | Impact if Missing |
|-------------|-------|------------|-------------------|
| Authentication | 1 | Medium | Anyone can admin |
| Stock Locking | 1 | Medium | Overselling guaranteed |
| Payment Integration | 1 | High | Can't make money |
| Redis Caching | 2 | Medium | DB dies under load |
| Rate Limiting | 2 | Low | Bot abuse |
| Background Jobs | 2 | Medium | Slow responses |
| DB Optimization | 2 | Medium | Slow queries |
| Idempotency | 3 | Medium | Duplicate charges |
| Audit Logging | 3 | Medium | No dispute resolution |
| Distributed Locking | 4 | High | Multi-server overselling |
| Queue Processing | 4 | High | Can't handle 100k users |
| Circuit Breakers | 4 | Medium | Cascade failures |
| Observability | 4 | High | Blind troubleshooting |
| Graceful Degradation | 4 | High | Total failure on partial outage |

---

> **Remember:** Each phase depends on the previous. Skipping phases creates technical debt that's expensive to fix later.
