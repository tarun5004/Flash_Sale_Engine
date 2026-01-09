🟢 PHASE 1 — PRODUCT DOMAIN (CURRENT FOCUS)
1️⃣ Product Core (MVP)

 Create product

 Update price

 Apply discount

 Get products (list + search) ⬅️ current

 Update stock

 Update product name

 Activate / Deactivate product

👉 Ye phase complete hua = Product CRUD complete

🟡 PHASE 2 — PRODUCT ADVANCED

 Product images (URL based, not upload first)

 Multiple images per product

 Soft delete (is_active = False)

 Product audit fields (updated_at)

🔵 PHASE 3 — USER DOMAIN

 User registration

 Login (JWT)

 User profile update

 Address management

🟣 PHASE 4 — ORDER & INVENTORY (FLASH SALE CORE)

 Create order

 Reserve stock (LOCK)

 Prevent overselling

 Order status (PENDING, PAID, FAILED)

 Rollback stock on failure

👉 Yahin tum Level-5 engineer banoge

🔴 PHASE 5 — PAYMENT & WORKERS

 Payment model

 Payment status tracking

 Background worker (Celery / RQ)

 Retry logic

 Idempotency

⚫ PHASE 6 — PERFORMANCE & SCALE

 Redis caching

 Pagination everywhere

 DB indexes

 Concurrency testing

 Rate limiting