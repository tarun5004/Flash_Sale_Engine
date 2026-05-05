# I'm Solo-Building a Flash Sale Engine From Scratch — Here's What Broke (and What I Learned)

---

**TL;DR:** I'm building a production-grade Flash Sale Engine — the kind of backend that powers those "Sale starts at 12 PM, stock gone by 12:00:03 PM" moments. Solo. No team. No tutorials. Just raw FastAPI, async SQLAlchemy, and an unhealthy amount of coffee.

Here's the real story — the bugs that humbled me, the design choices that taught me, and the roadmap that keeps me up at night.

---

## 🔥 Why a Flash Sale Engine?

Ever tried buying something on a Flipkart/Amazon flash sale? You click "Buy Now" at exactly 12:00:00, and by 12:00:01 it says "Out of Stock."

Behind that one-second experience is a system handling:
- 50,000+ concurrent users fighting for 100 items
- Stock that CANNOT oversell (not even by 1 unit)
- Payments that must either fully succeed or fully rollback
- A database that's screaming for its life

I thought: "How hard can it be?"

Narrator: *It was hard.*

---

## 🧱 The Stack (and Why)

| Choice | Why |
|--------|-----|
| **FastAPI** | Async-native, auto-docs, type hints = less bugs |
| **Async SQLAlchemy 2.0** | Non-blocking DB calls (because blocking = dead under load) |
| **SQLite + aiosqlite** | MVP first. Postgres migration is one config change away |
| **Pydantic v2** | Request validation that screams at you before bad data touches the DB |
| **Vanilla HTML/CSS/JS** | Frontend exists to demo. No React. No Next.js. Fight me. |

"Why not Django?"
Because I wanted to learn the hard way. And honestly? I learned more debugging async SQLAlchemy in 2 days than I did in 2 months of following Django tutorials.

---

## ✅ What's Built So Far (Phase 1 — Complete)

### Backend (25+ API routes, fully tested):

**Auth System**
- User registration with email uniqueness, bcrypt password hashing
- JWT login with token expiry
- `get_current_user` dependency that protects routes — no token, no entry

**Product Domain**
- Full CRUD — create, update, search, activate/deactivate
- 350 seeded products across 7 categories (Electronics, Fashion, Home, Beauty, Sports, Books, Toys)
- Single product detail endpoint with image support

**Order System (this is where it gets spicy 🌶️)**
- `SELECT FOR UPDATE` — database row locking to prevent overselling
- Atomic transactions: stock decrement + order creation + payment in ONE transaction
- Compensation pattern: payment fails? Stock rolls back. No ghost orders.
- Every 5th order intentionally fails (simulated payment gateway) to test the rollback path

**Cart System**
- Add, update quantity, remove items
- Full cart summary with product details
- Per-user isolation (your cart is yours)

**Payment Simulation**
- Simulated payment gateway with deliberate failures
- Because in real life, payment gateways fail. A lot. And if your system can't handle that, you're shipping refund emails at 3 AM.

### Frontend (Presentation-Grade Myntra-Inspired UI):
- 3-page SPA: Product Grid → Product Detail → Cart
- Live countdown timer ("Sale ends in 2h 34m 12s")
- Real-time stock bars that change color (green → orange → red → SOLD OUT)
- Search with debouncing, category filters, responsive grid
- Every API touchpoint has a `🔌 BACKEND:` comment showing exactly where `fetch()` calls replace localStorage

---

## 💀 The Bugs That Almost Broke Me

### 1. The Greenlet Error From Hell

```
MissingGreenlet: greenlet_spawn has not been called
```

If you've used async SQLAlchemy, you've seen this. If you haven't — count your blessings.

**What happened:** SQLAlchemy relationships use lazy loading by default. In sync mode, it just runs another query. In async mode? It PANICS. Because lazy loading is a synchronous operation trying to run inside an async context.

**Fix:** Every single relationship needed `lazy="selectin"` or `lazy="joined"`. Every. Single. One. I went through 6 model files, found the offenders, and added explicit eager loading.

**Lesson:** Async SQLAlchemy is powerful, but it doesn't hold your hand. It hands you a loaded gun and says "good luck."

### 2. bcrypt Went to Version 5 and Chose Violence

```
AttributeError: module 'bcrypt' has no attribute '__about__'
```

Installed the latest bcrypt (5.x). Passlib (the library that wraps bcrypt) still expects bcrypt 4.x internals.

**Fix:** `pip install bcrypt==4.2.1`

One line. Took me 45 minutes to figure out.

**Lesson:** In the Python ecosystem, "latest" doesn't mean "compatible." Pin your dependencies, or they'll pin you to your desk at midnight.

### 3. The Tuple That SQLAlchemy Wouldn't Forgive

```python
# This works for a list:
__table_args__ = (UniqueConstraint("user_id", "product_id"),)

# This does NOT:
__table_args__ = (UniqueConstraint("user_id", "product_id"))
```

Notice the trailing comma? That tiny `,` is the difference between a tuple and a parenthesized expression. Without it, SQLAlchemy tries to interpret your constraint as the table args directly, and gives you the most cryptic error you've ever read.

Python moment. 🐍

### 4. Lazy Loading + Pydantic = Silent Data Loss

Order placed successfully. Response returned. But `order.product` was `None`.

**Why?** After the transaction committed, SQLAlchemy expired all attributes (default behavior). When Pydantic tried to serialize the product relationship, it was already detached from the session.

**Fixes (two layers):**
- `expire_on_commit=False` on the session factory
- `joinedload(Order.product)` in every query that needs relationships

This one was subtle. No error. No crash. Just missing data in the response. The worst kind of bug — the silent one.

### 5. The Orphan Method Living Outside Its Class

Found a method in `product_repo.py` that was defined OUTSIDE the ProductRepo class. Just... floating there. Python didn't complain. The file imported fine. But calling it? `NameError: 'self' is not defined`.

Indentation-based languages are beautiful until they're not.

---

## 🏗️ Architecture Decisions (and Why They Matter)

### Layered Monolith with Repository Pattern

```
Router → Service → Repository → Model → Database
```

- **Routers** know HTTP, not business logic
- **Services** know business rules, not SQL
- **Repositories** know queries, not business rules
- **Models** know schema, not behavior

"Why not microservices?"

Because when User A buys the last iPhone, the stock decrement AND order creation MUST happen in ONE database transaction. In microservices, that requires distributed transactions (saga pattern), which adds latency and complexity. 

A monolith with clean separation scales to 100k+ users. Microservices become worth it when your TEAM scales past 50 engineers, not when your traffic does.

### SELECT FOR UPDATE (Pessimistic Locking)

This is the heart of any flash sale system:

```sql
BEGIN;
SELECT * FROM products WHERE id = 42 FOR UPDATE;  -- Lock this row
-- Only ONE transaction can hold this lock
UPDATE products SET stock = stock - 1 WHERE id = 42;
INSERT INTO orders (...);
COMMIT;  -- Release lock
```

Without this, 100 users buying the last 1 item = 100 successful orders. With this, 1 succeeds and 99 get "Out of Stock" instantly.

### Compensation Pattern (Not Just Rollback)

```
Stock locked → Order created → Payment called → Payment FAILS
Now what?
```

You can't just `rollback` because the stock was decremented in a committed transaction. You need a COMPENSATION: explicitly increment stock back, mark order as FAILED.

My system does this automatically. I even made every 5th payment fail on purpose to prove it works. Trust but verify.

---

## 🚀 What's Coming Next

### Phase 2: Scale-Ready (the fun stuff)

| Feature | Why |
|---------|-----|
| **Redis Caching** | 100k users loading the product page = 100k DB queries. With Redis? 1 DB query + 99,999 cache hits. |
| **Rate Limiting** | Without it, one dude with a script buys everything before real humans can blink |
| **Celery Workers** | Payment processing shouldn't block the HTTP response. Fire and forget, confirm later. |
| **Database Indexes** | Right now my queries work. Under load? They'll crawl. Indexing before scaling. |
| **Pagination** | Returning 350 products in one response is fine for demos. In production? That's a 2MB JSON payload. No. |

### Phase 3: Production-Hardening

| Feature | Why |
|---------|-----|
| **Idempotency Keys** | User clicks "Pay" twice because the page froze? Without idempotency, that's two charges. With it, same result. |
| **Concurrency Testing** | I'll throw 10,000 simultaneous requests at 10 items. If stock goes negative, I failed. |
| **Soft Deletes** | `DELETE FROM products` is permanent. `is_active = False` is recoverable. |
| **Audit Trails** | "Who changed the price at 3 AM?" — Every mutation logged. |

### Phase 4: Enterprise-Grade (the dream)

| Feature | Why |
|---------|-----|
| **Distributed Locking (Redis)** | Multiple server instances = database row locks aren't enough |
| **Event Sourcing** | Don't just store current state — store every event that led to it |
| **Circuit Breakers** | Payment gateway down? Stop sending requests instead of failing 10,000 times |
| **Queue-Based Orders** | Accept order → put in queue → process async. Handle 100k+ concurrent purchases |
| **Prometheus + Grafana** | If you can't measure it, you can't improve it |

---

## 📊 By The Numbers

| Metric | Value |
|--------|-------|
| Files changed | 24 |
| Lines added | 3,066 |
| Lines deleted | 91 |
| API routes | 25+ |
| Models | 6 (Product, User, Order, Payment, CartItem, ProductImage) |
| Demo products | 350 across 7 categories |
| Bugs that made me question my career | At least 5 |
| Stack Overflow tabs open simultaneously | 14 (new personal record) |
| Times I said "it works on my machine" | Lost count |

---

## 🎯 The Real Takeaway

Building this solo taught me something no tutorial ever could:

**Production systems aren't about making things work. They're about making things NOT break.**

Anyone can build a `/buy` endpoint that decrements stock. The real engineering is:
- What happens when two people buy the last item at the same millisecond?
- What happens when payment succeeds but the database write fails?
- What happens when your ORM silently returns `None` instead of raising an error?
- What happens when a library update breaks a dependency you didn't even know existed?

These aren't edge cases in a flash sale. These are the NORMAL cases.

---

## 🔗 Check It Out

The entire codebase is open source — models, services, repositories, the Myntra-inspired demo UI, the 100+ page architecture docs. All of it.

**GitHub:** [github.com/tarun5004/Flash_Sale_Engine](https://github.com/tarun5004/Flash_Sale_Engine)

If you've ever had to deal with race conditions, async ORMs, or payment rollbacks — you know the pain. Drop a comment with your worst concurrency bug story. I'll go first: mine involved `stock = -3`. Yes, negative three. We don't talk about that commit.

---

*Currently building in public. Phase 2 (Redis + Rate Limiting + Celery) starts next. Follow along if you want to see a solo dev fight distributed systems and (occasionally) win.*

#SoftwareEngineering #Python #FastAPI #BackendDevelopment #FlashSale #SystemDesign #BuildInPublic #AsyncProgramming #SQLAlchemy #WebDevelopment #OpenSource #SoloDev
