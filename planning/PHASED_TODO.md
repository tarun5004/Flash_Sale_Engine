# Flash Sale Engine — Phased TODO

> Original TODOs reorganized by deployment readiness, not by domain.
> Each phase builds on the previous — complete Phase 1 before moving to Phase 2.

---

## 🟢 Phase 1: MVP / Must-Have
> **Goal:** Basic working flash sale that doesn't break under normal load.
> **Deploy after:** Can handle 1-10 concurrent users safely.

| # | Task | Original Phase | Why Phase 1 |
|---|------|----------------|-------------|
| 1 | Create product | Product Core | Can't sell without products |
| 2 | Update price | Product Core | Basic admin operation |
| 3 | Apply discount | Product Core | Flash sale = discounts |
| 4 | Get products (list + search) | Product Core | Users need to browse |
| 5 | Update stock | Product Core | Inventory management essential |
| 6 | Update product name | Product Core | Basic CRUD |
| 7 | Activate / Deactivate product | Product Core | Control what's visible |
| 8 | User registration | User Domain | Need users to place orders |
| 9 | Login (JWT) | User Domain | Authentication required before orders |
| 10 | Create order | Order & Inventory | Core purchase flow |
| 11 | Reserve stock (LOCK) | Order & Inventory | Prevent overselling from day 1 |
| 12 | Prevent overselling | Order & Inventory | Flash sale without this = disaster |
| 13 | Order status (PENDING, PAID, FAILED) | Order & Inventory | Track order lifecycle |
| 14 | Payment model | Payment & Workers | Can't complete purchase without payment |
| 15 | Payment status tracking | Payment & Workers | Know if payment succeeded |

**Phase 1 delivers:** A user can register → login → browse products → place order → pay.

---

## 🟡 Phase 2: Scale-Ready
> **Goal:** Handle flash sale traffic spikes without crashing.
> **Deploy after:** Can handle 100-1000 concurrent users.

| # | Task | Original Phase | Why Phase 2 |
|---|------|----------------|-------------|
| 1 | Redis caching | Performance & Scale | DB will die under load without cache |
| 2 | Pagination everywhere | Performance & Scale | Large result sets kill performance |
| 3 | DB indexes | Performance & Scale | Slow queries = timeouts under load |
| 4 | Rate limiting | Performance & Scale | Prevent abuse, protect resources |
| 5 | Rollback stock on failure | Order & Inventory | Data consistency during failures |
| 6 | Retry logic | Payment & Workers | Network failures are common at scale |
| 7 | Background worker (Celery / RQ) | Payment & Workers | Offload heavy tasks from request cycle |

**Phase 2 delivers:** System survives traffic spikes, recovers from failures gracefully.

---

## 🟠 Phase 3: Production-Hardening
> **Goal:** Secure, observable, maintainable in production.
> **Deploy after:** Ready for real users with real money.

| # | Task | Original Phase | Why Phase 3 |
|---|------|----------------|-------------|
| 1 | Idempotency | Payment & Workers | Prevent duplicate charges/orders |
| 2 | Concurrency testing | Performance & Scale | Validate race condition fixes |
| 3 | Product images (URL based) | Product Advanced | Better UX, not blocking MVP |
| 4 | Multiple images per product | Product Advanced | Enhanced product display |
| 5 | Soft delete (is_active = False) | Product Advanced | Data retention, audit compliance |
| 6 | Product audit fields (updated_at) | Product Advanced | Track changes for debugging |
| 7 | User profile update | User Domain | Nice-to-have, not critical for purchase |
| 8 | Address management | User Domain | Required for shipping, not for digital goods |

**Phase 3 delivers:** Production-safe system with proper audit trails and data integrity.

---

## 🔴 Phase 4: Enterprise-Grade
> **Goal:** Multi-region, high-availability, compliance-ready.
> **Deploy after:** Handling 10k+ concurrent users, enterprise customers.

| # | Task | Original Phase | Why Phase 4 |
|---|------|----------------|-------------|
| 1 | Distributed locking (Redis-based) | — | Multi-instance deployment |
| 2 | Database read replicas | — | Separate read/write traffic |
| 3 | Event sourcing / audit log | — | Compliance, debugging at scale |
| 4 | Admin role-based access | — | Enterprise security requirements |
| 5 | Webhook retry with exponential backoff | — | Reliable integrations |
| 6 | Metrics & observability (Prometheus) | — | SLA monitoring |
| 7 | Circuit breakers | — | Graceful degradation |
| 8 | Queue-based order processing | — | Handle 100k+ concurrent purchases |

**Phase 4 delivers:** Enterprise SLA, compliance, and global scale capabilities.

---

## 📊 Progress Tracking

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1: MVP | 🟡 In Progress | ~50% (Product CRUD done, Auth + Orders pending) |
| Phase 2: Scale | ⬜ Not Started | 0% |
| Phase 3: Hardening | ⬜ Not Started | 0% |
| Phase 4: Enterprise | ⬜ Not Started | 0% |

---

## 🎯 Current Focus

**Complete Phase 1 first:**
1. ✅ Product CRUD — Done
2. ⬜ User registration + Login (JWT)
3. ⬜ Order creation with stock locking
4. ⬜ Basic payment flow

> **Rule:** No Phase 2 work until Phase 1 is 100% complete.
