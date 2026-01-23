# Deep Dive: Stock Reservation & Locking

> A comprehensive guide to preventing overselling in flash sale systems.

---

## Table of Contents

1. [Theory Behind It](#theory-behind-it)
2. [Real-World Example](#real-world-example-xiaomi-flash-sale-disaster-2014)
3. [Failure Scenarios](#failure-scenarios)
4. [Common Mistakes Engineers Make](#common-mistakes-engineers-make)
5. [How to Validate Correctness in Production](#how-to-validate-correctness-in-production)

---

## Theory Behind It

### The Fundamental Problem: Concurrent Access to Shared State

Stock is a **shared mutable resource**. Multiple processes (user requests) want to read and modify it simultaneously. This creates a classic computer science problem: **race conditions**.

**Race condition definition:**
> When the outcome of a program depends on the sequence or timing of uncontrollable events (like thread scheduling or network latency).

### The Read-Modify-Write Problem

Every purchase involves three steps:
1. **Read** current stock
2. **Check** if stock >= requested quantity
3. **Write** new stock (stock - quantity)

The problem: These three steps are NOT atomic. Between step 1 and step 3, another request can execute its own step 1.

```
Timeline (microseconds):
────────────────────────────────────────────────────────
Time    User A                    User B
────────────────────────────────────────────────────────
T0      READ stock → 1            
T1                                READ stock → 1
T2      CHECK: 1 >= 1? YES        
T3                                CHECK: 1 >= 1? YES
T4      WRITE: stock = 0          
T5                                WRITE: stock = -1  ❌
────────────────────────────────────────────────────────
```

Both users "saw" stock = 1. Both proceeded. Result: **oversold by 1 unit**.

### Why This Gets Worse at Scale

Probability of collision increases with:
- **Concurrency level** — More simultaneous requests
- **Transaction duration** — Longer time between read and write
- **Hotspot data** — Popular products get more concurrent access

Flash sale reality:
- 100,000 users
- 100 items in stock
- All clicking "Buy" at exactly 12:00:00

This isn't a theoretical edge case. It's the **guaranteed normal scenario**.

### Isolation Levels (Database Theory)

Databases provide isolation levels to handle concurrent access:

| Level | Dirty Read | Non-Repeatable Read | Phantom Read | Performance |
|-------|------------|---------------------|--------------|-------------|
| READ UNCOMMITTED | Possible | Possible | Possible | Fastest |
| READ COMMITTED | Prevented | Possible | Possible | Fast |
| REPEATABLE READ | Prevented | Prevented | Possible | Medium |
| SERIALIZABLE | Prevented | Prevented | Prevented | Slowest |

**Problem:** Even SERIALIZABLE doesn't prevent our issue automatically. We need **explicit locking**.

### Types of Locks

**Pessimistic Locking:**
> "I assume conflict will happen. Lock the resource before touching it."

- `SELECT ... FOR UPDATE` — Exclusive lock on selected rows
- `SELECT ... FOR SHARE` — Shared lock (multiple readers, no writers)
- Blocks other transactions until lock released

**Optimistic Locking:**
> "I assume conflict is rare. Detect it after the fact and retry."

- Add `version` column to table
- Read: `SELECT stock, version FROM products WHERE id = 1`
- Update: `UPDATE products SET stock = 9, version = 2 WHERE id = 1 AND version = 1`
- If `rows_affected = 0`, someone else modified it → retry

**Which to use for flash sale?**

Pessimistic for stock (high contention guaranteed). Optimistic for user profiles (low contention).

---

## Real-World Example: Xiaomi Flash Sale Disaster (2014)

**Context:** Xiaomi sold phones through flash sales in India. Limited stock, massive demand.

**What happened:**
- 100,000 phones available
- 500,000+ users trying to buy at exact same second
- System showed "Order Confirmed" to many users
- Actual stock depleted almost instantly
- 40,000+ users received confirmation but no phone

**Root cause analysis:**
1. Stock check was separate from stock decrement
2. Confirmation shown before payment completed
3. No pessimistic locking on stock
4. Eventual consistency used where strong consistency was needed

**Aftermath:**
- Massive customer backlash
- Social media firestorm
- Trust damaged
- Had to honor some orders at a loss

**Lesson:** Stock locking isn't optional for flash sales. It's the foundation.

---

## Failure Scenarios

### Scenario 1: Lock Timeout Under Load

**Setup:**
- 10,000 concurrent purchase requests
- Each holds lock for 100ms (payment processing)
- Database lock timeout = 5 seconds

**What happens:**
```
Request 1: Acquires lock at T0
Request 2: Waits for lock at T0.001
Request 3: Waits for lock at T0.002
...
Request 50: Waits for lock at T0.050
Request 51: Still waiting at T5.000 → LOCK TIMEOUT ERROR
```

**Result:**
- Users see "Something went wrong"
- No purchase completed
- Retries make it worse

**Mitigation:**
- Reduce lock hold time (decouple payment from stock lock)
- Use queue to serialize requests
- Show "Processing" instead of blocking

---

### Scenario 2: Deadlock Between Orders

**Setup:**
- User A wants Product 1 + Product 2 (bundle)
- User B wants Product 2 + Product 1 (bundle)

**What happens:**
```
User A: Lock Product 1 ✅
User B: Lock Product 2 ✅
User A: Try to lock Product 2 → WAITING (B holds it)
User B: Try to lock Product 1 → WAITING (A holds it)
```

**Result:** Both stuck forever (deadlock). Database eventually kills one.

**Mitigation:**
- Always lock resources in consistent order (by product ID ascending)
- Set lock timeout to detect and recover
- Avoid multi-resource locks in hot paths

---

### Scenario 3: Lost Update After Lock Release

**Setup:**
- Lock acquired, stock decremented, commit successful
- Payment processing happens AFTER commit
- Payment fails

**What happens:**
```
T0: Lock product, decrement stock 100 → 99, COMMIT
T1: Release lock
T2: Process payment with gateway
T3: Payment declined (insufficient funds)
T4: Need to restore stock... but lock already released!
T5: Another user already bought using stock 99
T6: Restore stock 99 → 100... but someone has stock 99's order!
```

**Result:** Inventory numbers meaningless. Oversold or undersold.

**Mitigation:**
- Never release lock until entire transaction (including payment) completes
- OR use "reservation" model: reserved_stock separate from available_stock
- OR use saga pattern with compensation

---

### Scenario 4: Long Lock Hold During Network Partition

**Setup:**
- Request acquires lock
- Network partition between app and database
- App thinks transaction is ongoing
- Database thinks connection dropped

**What happens:**
- Database releases lock after connection timeout
- App still thinks it holds lock, continues processing
- Another request acquires same lock
- Both complete → oversold

**Mitigation:**
- Use transaction timeouts shorter than connection timeouts
- Implement fencing tokens (monotonic transaction IDs)
- Verify lock ownership before final commit

---

## Common Mistakes Engineers Make

### Mistake 1: Locking After Reading

```
❌ Wrong:
product = await db.get_product(id)  # No lock
if product.stock >= quantity:
    product = await db.get_product_for_update(id)  # Lock now
    product.stock -= quantity
```

Race condition exists between first read and lock acquisition.

```
✅ Correct:
product = await db.get_product_for_update(id)  # Lock FIRST
if product.stock >= quantity:
    product.stock -= quantity
```

---

### Mistake 2: Check Outside Transaction

```
❌ Wrong:
# Transaction 1
stock = await get_stock(product_id)

# No transaction
if stock >= quantity:
    # Transaction 2
    await decrement_stock(product_id, quantity)
```

Two transactions = two separate isolation contexts.

```
✅ Correct:
async with db.begin():  # Single transaction
    stock = await get_stock_for_update(product_id)
    if stock >= quantity:
        await decrement_stock(product_id, quantity)
```

---

### Mistake 3: Assuming ORM Handles It

```
❌ Wrong assumption:
product.stock -= 1
await session.commit()
# "SQLAlchemy will handle concurrency"
```

ORM does NOT automatically add locks. This is just:
```sql
UPDATE products SET stock = 99 WHERE id = 1
```

If two requests read 100, both write 99. Stock should be 98.

```
✅ Correct:
# Explicit lock
product = await session.execute(
    select(Product).where(Product.id == 1).with_for_update()
)
```

---

### Mistake 4: Using Application-Level Locks for Database Operations

```
❌ Wrong:
import threading
lock = threading.Lock()

with lock:
    product = await db.get_product(id)
    product.stock -= 1
    await db.commit()
```

**Why wrong:**
- Only works on single server
- Multiple app instances = multiple locks = no coordination
- Database is shared, app memory is not

```
✅ Correct:
Use database-level lock (FOR UPDATE) or distributed lock (Redis).
```

---

### Mistake 5: Locking Too Broadly

```
❌ Wrong:
# Lock entire table
await db.execute("LOCK TABLE products IN EXCLUSIVE MODE")
```

One iPhone purchase blocks all Samsung purchases.

```
✅ Correct:
# Lock only the specific row
await db.execute(
    select(Product).where(Product.id == iphone_id).with_for_update()
)
```

---

### Mistake 6: Silent Failure on Lock Conflict

```
❌ Wrong:
try:
    await purchase_with_lock(product_id)
except LockError:
    pass  # Silently fail
```

User thinks nothing happened, clicks again, creates confusion.

```
✅ Correct:
except LockError:
    raise HTTPException(
        status_code=503,
        detail="High demand. Please try again in a moment.",
        headers={"Retry-After": "2"}
    )
```

---

## How to Validate Correctness in Production

### Validation 1: The Invariant Check

**Invariant:** At any point in time:
```
initial_stock = current_stock + sum(order_quantities) + sum(failed_refunds)
```

**Implementation:**
- Scheduled job every minute
- Compare: `products.stock + SUM(orders.quantity WHERE status=PAID)`
- Alert if doesn't match initial stock

**What it catches:**
- Overselling (stock went negative conceptually)
- Lost orders (stock decremented but order missing)
- Double refunds (stock over-restored)

---

### Validation 2: Concurrent Load Test

**Setup:**
- Create product with stock = 100
- Launch 1000 concurrent purchase requests (10x stock)
- Each request tries to buy 1 unit

**Expected result:**
- Exactly 100 orders with status = PAID
- Exactly 900 orders with status = FAILED (out of stock)
- Final stock = 0
- No negative stock ever (check logs)

**How to run:**
```
Tool: Locust, k6, or wrk
Scenario: All requests start at exact same time (use barrier)
Duration: Run for 30 seconds with sustained load
```

**Red flags:**
- Orders created > 100 (oversold)
- Stock < 0 at any log entry
- Orders created < 100 with stock > 0 (under-sold, lock issues)

---

### Validation 3: Chaos Engineering

**Test 1: Kill database connection mid-transaction**
- Start purchase
- Kill connection before commit
- Verify: No partial state (order without stock decrement)

**Test 2: Network latency injection**
- Add 5 second delay between app and DB
- Verify: Timeouts handled gracefully
- Verify: No double-execution on retry

**Test 3: Database failover**
- Switch to replica during purchase
- Verify: Transaction fails cleanly, user can retry

---

### Validation 4: Audit Log Analysis

**Every stock change should have:**
- Before value
- After value
- Actor (user/system)
- Timestamp
- Related order ID

**Query to find anomalies:**
```sql
SELECT 
    p.id,
    p.stock as current_stock,
    initial.stock as initial_stock,
    (SELECT SUM(quantity) FROM orders WHERE product_id = p.id AND status = 'PAID') as sold,
    initial.stock - p.stock as stock_change,
    (initial.stock - p.stock) - COALESCE((SELECT SUM(quantity) FROM orders WHERE product_id = p.id AND status = 'PAID'), 0) as discrepancy
FROM products p
JOIN product_initial_stock initial ON p.id = initial.product_id
WHERE ABS(discrepancy) > 0;
```

Any non-zero discrepancy = bug.

---

### Validation 5: Production Monitoring Dashboards

**Metrics to track:**

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| Lock wait time (p99) | < 100ms | 100-500ms | > 500ms |
| Lock timeout rate | 0% | < 1% | > 1% |
| Stock < 0 events | 0 | 0 | > 0 (immediate alert) |
| Order/stock mismatch | 0 | 0 | > 0 (immediate alert) |
| Failed purchases (out of stock) | Varies | N/A | N/A |

**Alert rules:**
- `stock < 0` → PagerDuty immediately
- Lock timeout > 5% for 1 minute → Slack alert
- Stock mismatch > 0 → Stop flash sale, investigate

---

## Summary

Stock locking is not just "add FOR UPDATE". It's a system design problem involving:

1. **Transaction boundaries** — Where does the critical section start and end?
2. **Lock granularity** — Row vs table vs distributed?
3. **Failure handling** — What happens when lock times out?
4. **Recovery** — How to restore consistency after failure?
5. **Validation** — How to prove it works under real load?

The theory is simple. The implementation is tricky. The validation is where most teams skip—and regret it during their first real flash sale.

---

## Next Steps

After mastering stock locking, these topics build on it:
- **Idempotency System** — Prevent duplicate orders from retries
- **Payment Integration** — Coordinate stock and payment atomically
- **Distributed Locking** — Scale beyond single database instance
