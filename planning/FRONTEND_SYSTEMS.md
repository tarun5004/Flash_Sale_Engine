# Frontend Systems Specification

> **Purpose**: Define frontend requirements, API contracts, and behavioral specifications for Flash Sale Engine.  
> **Audience**: Frontend engineers, full-stack developers, API designers.  
> **Scope**: Systems and contracts only. No UI code, no framework selection.

---

## Table of Contents

1. [System Context](#system-context)
2. [API Contract Requirements](#api-contract-requirements)
3. [Authentication Flow](#authentication-flow)
4. [Flash Sale Event Lifecycle](#flash-sale-event-lifecycle)
5. [Real-Time Requirements](#real-time-requirements)
6. [Error Handling Contract](#error-handling-contract)
7. [Offline & Degraded Mode](#offline--degraded-mode)
8. [Performance Budgets](#performance-budgets)
9. [State Management Patterns](#state-management-patterns)
10. [Testing Requirements](#testing-requirements)

---

## System Context

### What the Frontend Must Handle

```
┌─────────────────────────────────────────────────────────────┐
│                     FLASH SALE EVENT                        │
│                                                             │
│   10:00:00.000 - Sale starts                               │
│   10:00:00.050 - 50,000 users click "Buy Now"              │
│   10:00:00.500 - Stock depleted                            │
│   10:00:01.000 - 49,900 users see "Sold Out"               │
│                                                             │
│   Window: 500 milliseconds                                  │
│   Success rate: 0.2%                                        │
│   User emotion: Frustration if slow/unfair                  │
└─────────────────────────────────────────────────────────────┘
```

### Frontend Responsibilities

| Responsibility | Why |
|----------------|-----|
| Accurate countdown | Users must see identical sale start time |
| Instant feedback | Sub-100ms response to click |
| Graceful failure | "Sold out" not "Error occurred" |
| Queue position (future) | Fairness perception |
| Idempotent requests | Prevent accidental double-orders |

### Frontend Non-Responsibilities

| Handled By Backend | Why |
|--------------------|-----|
| Stock validation | Client can't be trusted |
| Price calculation | Security |
| Order finalization | ACID guarantees |
| Payment processing | PCI compliance |

---

## API Contract Requirements

### Base URL Structure

```
Production:  https://api.flashsale.example.com/v1
Staging:     https://api-staging.flashsale.example.com/v1
Development: http://localhost:8000/v1
```

### Request Headers

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
Accept: application/json
X-Idempotency-Key: <uuid>          # Required for POST /orders
X-Client-Version: 1.2.3            # For compatibility tracking
X-Request-ID: <uuid>               # For distributed tracing
```

### Standard Response Envelope

All API responses follow this structure:

```json
// Success
{
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:00:00.123Z"
  }
}

// Error
{
  "error": {
    "code": "OUT_OF_STOCK",
    "message": "Product is sold out",
    "details": { ... }
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:00:00.123Z"
  }
}
```

### Pagination Contract

```json
{
  "data": [ ... ],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

### Required Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | /auth/register | User registration | No |
| POST | /auth/login | Get tokens | No |
| POST | /auth/refresh | Refresh access token | No |
| GET | /auth/me | Current user profile | Yes |
| GET | /products | List products | Optional |
| GET | /products/{id} | Product details | Optional |
| GET | /products/{id}/stock | Real-time stock | Optional |
| POST | /orders | Place order | Yes |
| GET | /orders | User's orders | Yes |
| GET | /orders/{id} | Order details | Yes |
| POST | /orders/{id}/cancel | Cancel order | Yes |

---

## Authentication Flow

### Token Lifecycle

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Login     │────▶│ Access Token │────▶│   API Call   │
│              │     │  (15 min)    │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼ expires
                     ┌──────────────┐
                     │   Refresh    │
                     │   Token      │
                     │  (7 days)    │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ New Access   │
                     │   Token      │
                     └──────────────┘
```

### Token Storage Requirements

```
Access Token:
  - Store in memory only
  - Never in localStorage (XSS risk)
  - Never in cookies without HttpOnly
  - Lost on page refresh (acceptable)

Refresh Token:
  - HttpOnly cookie (set by backend)
  - Secure flag in production
  - SameSite=Strict
  - Cannot be read by JavaScript
```

### Login Request

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

### Login Response

```json
{
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 900,
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe"
    }
  }
}
```

### Token Refresh Flow

```
1. API returns 401 Unauthorized
2. Check if refresh token exists (in cookie)
3. If yes: POST /auth/refresh
4. If refresh succeeds: Retry original request
5. If refresh fails: Redirect to login
```

### Pre-Authentication for Flash Sale

Users must be authenticated BEFORE sale starts:

```
❌ Wrong: User logs in at 10:00:00 (sale start)
          → Login takes 500ms
          → Stock gone by 10:00:00.500

✅ Right: User logs in at 9:55:00
          → Session ready
          → Click "Buy" at 10:00:00.001
```

Frontend must:
- Prompt login 5+ minutes before sale
- Show "Login required to participate" on sale page
- Disable "Buy" button if not authenticated

---

## Flash Sale Event Lifecycle

### Event States

```
UPCOMING → STARTING → ACTIVE → ENDING → ENDED
    │          │         │         │        │
    │          │         │         │        └─ Show results
    │          │         │         └─ Last-chance messaging
    │          │         └─ Buy button enabled
    │          └─ Countdown final seconds
    └─ Show countdown timer
```

### State Transitions

| Current State | Trigger | Next State | Frontend Action |
|---------------|---------|------------|-----------------|
| UPCOMING | T-10 seconds | STARTING | Show final countdown |
| STARTING | T=0 | ACTIVE | Enable purchase |
| ACTIVE | Stock=0 OR time limit | ENDING | Disable purchase |
| ENDING | 30 seconds elapsed | ENDED | Show summary |

### Countdown Timer Requirements

**Problem**: Client clocks are unreliable.

```
User A's clock: 09:59:58 (2 sec fast)
User B's clock: 10:00:02 (2 sec slow)
Server time:    10:00:00

User A clicks "Buy" at their 10:00:00 → Server: 09:59:58 → "Sale not started"
User B waits until their 10:00:00 → Server: 10:00:02 → Stock already gone
```

**Solution**: Server time synchronization.

```
1. On page load: GET /time → { "server_time": "2024-01-15T09:55:00.123Z" }
2. Calculate offset: offset = server_time - client_time
3. Display countdown using: client_time + offset
4. Re-sync every 60 seconds
5. Re-sync on visibility change (tab becomes active)
```

### Countdown Display Rules

| Time Remaining | Display Format | Update Frequency |
|----------------|----------------|------------------|
| > 1 hour | "2h 30m" | Every minute |
| 1-60 minutes | "45:30" | Every second |
| < 60 seconds | "00:45.3" | Every 100ms |
| < 10 seconds | "00:05.234" | Every 16ms (60fps) |

### Stock Display Requirements

```
Real stock count: 100 units
Display options:

Option A (Exact): "100 left"
  - Pros: Accurate
  - Cons: Creates anxiety, "only 3 left" causes rage-clicking

Option B (Buckets): "Limited stock"
  - Pros: Less anxiety
  - Cons: Less informative

Option C (Threshold):
  - > 100: "In stock"
  - 10-100: "Limited stock"
  - < 10: "Almost gone"
  - 0: "Sold out"

Recommendation: Option C for flash sales
```

---

## Real-Time Requirements

### When Real-Time is Needed

| Data | Real-Time? | Method | Latency Target |
|------|------------|--------|----------------|
| Stock count | Yes | WebSocket/SSE | < 500ms |
| Order status | Yes | WebSocket/SSE | < 2s |
| Sale start | Yes | WebSocket/SSE | < 100ms |
| Product list | No | Polling (5min) | N/A |
| User profile | No | On-demand | N/A |

### WebSocket Contract

**Connection URL:**
```
wss://api.flashsale.example.com/ws?token=<jwt>
```

**Message Format:**
```json
{
  "type": "stock_update",
  "data": {
    "product_id": "uuid",
    "stock": 45,
    "timestamp": "2024-01-15T10:00:00.123Z"
  }
}
```

**Event Types:**
```
stock_update     - Stock level changed
sale_started     - Flash sale began
sale_ended       - Flash sale ended
order_confirmed  - User's order confirmed
order_failed     - User's order failed
```

**Reconnection Strategy:**
```
1. Connection lost
2. Wait 1 second
3. Attempt reconnect
4. If failed: Wait 2 seconds (exponential backoff)
5. Max wait: 30 seconds
6. After 5 failures: Show "Connection lost" banner
7. On reconnect: Re-sync full state
```

### Server-Sent Events Alternative

If WebSocket infrastructure unavailable:

```
GET /events/stream
Accept: text/event-stream

Response:
data: {"type": "stock_update", "product_id": "uuid", "stock": 45}

data: {"type": "sale_started", "product_id": "uuid"}
```

### Polling Fallback

If real-time connections fail:

```
GET /products/{id}/stock

Poll interval:
  - Before sale: Every 30 seconds
  - During sale: Every 2 seconds
  - After sale: Stop polling
```

---

## Error Handling Contract

### Error Code Taxonomy

```
Authentication Errors (401)
  - TOKEN_EXPIRED
  - TOKEN_INVALID
  - TOKEN_MISSING

Authorization Errors (403)
  - FORBIDDEN
  - ADMIN_REQUIRED

Validation Errors (400)
  - INVALID_INPUT
  - MISSING_FIELD
  - INVALID_FORMAT

Business Logic Errors (409)
  - OUT_OF_STOCK
  - SALE_NOT_STARTED
  - SALE_ENDED
  - PURCHASE_LIMIT_EXCEEDED
  - ORDER_ALREADY_CANCELLED

Rate Limiting (429)
  - RATE_LIMIT_EXCEEDED

Server Errors (500/502/503)
  - INTERNAL_ERROR
  - SERVICE_UNAVAILABLE
```

### Error Response Examples

**Validation Error:**
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Validation failed",
    "details": {
      "fields": {
        "quantity": "Must be between 1 and 10",
        "email": "Invalid email format"
      }
    }
  }
}
```

**Business Logic Error:**
```json
{
  "error": {
    "code": "OUT_OF_STOCK",
    "message": "Product is sold out",
    "details": {
      "product_id": "uuid",
      "requested": 2,
      "available": 0
    }
  }
}
```

**Rate Limit Error:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "retry_after": 30,
      "limit": 10,
      "window": 60
    }
  }
}
```

### Frontend Error Display Rules

| Error Code | User Message | Action |
|------------|--------------|--------|
| OUT_OF_STOCK | "Sold out! Better luck next time." | Disable button |
| SALE_NOT_STARTED | "Sale starts in {countdown}" | Show timer |
| PURCHASE_LIMIT_EXCEEDED | "Maximum {n} per customer" | Show limit |
| RATE_LIMIT_EXCEEDED | "Please wait {n} seconds" | Disable + countdown |
| TOKEN_EXPIRED | (silent) | Auto-refresh |
| INTERNAL_ERROR | "Something went wrong. Please retry." | Retry button |
| SERVICE_UNAVAILABLE | "High demand. Retrying..." | Auto-retry with backoff |

### Retry Logic

```
Retryable errors:
  - 429 (after retry_after seconds)
  - 500 (with exponential backoff)
  - 502, 503, 504 (with exponential backoff)
  - Network errors (with exponential backoff)

Non-retryable errors:
  - 400 (fix input and resubmit)
  - 401 (re-authenticate)
  - 403 (no permission)
  - 409 (business rule violation)

Retry strategy:
  Attempt 1: Immediate
  Attempt 2: Wait 1s
  Attempt 3: Wait 2s
  Attempt 4: Wait 4s
  Max attempts: 4
  Max wait: 10s
```

---

## Offline & Degraded Mode

### Offline Detection

```
navigator.onLine = false
  OR
WebSocket disconnected + API request fails
  OR
API returns 503 consistently
```

### Offline Behavior

| Feature | Offline Behavior |
|---------|------------------|
| Product browsing | Show cached data |
| Countdown timer | Continue (synced before) |
| Buy button | Disable with message |
| Login | Disable with message |
| Order history | Show cached |
| Order placement | Queue for retry (risky) |

### Degraded Mode (Backend Overloaded)

**Symptoms:**
- High latency (> 2s)
- Intermittent 503 errors
- WebSocket disconnections

**Frontend Response:**
```
1. Show "High demand" indicator
2. Increase timeout to 10s
3. Reduce polling frequency
4. Queue non-critical requests
5. Show cached stock (with "may be outdated" warning)
```

### Recovery

```
1. Detect online/recovered
2. Re-establish WebSocket
3. Sync server time
4. Refresh critical state (stock, order status)
5. Resume normal operation
```

---

## Performance Budgets

### Page Load Targets

| Metric | Target | Maximum |
|--------|--------|---------|
| First Contentful Paint | < 1.0s | 1.5s |
| Largest Contentful Paint | < 2.0s | 2.5s |
| Time to Interactive | < 2.5s | 3.5s |
| Total Bundle Size (gzipped) | < 150KB | 200KB |
| JavaScript Bundle | < 100KB | 150KB |
| CSS Bundle | < 30KB | 50KB |

### Runtime Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Click to request sent | < 50ms | 100ms |
| API response processing | < 20ms | 50ms |
| UI update after response | < 16ms | 33ms |
| Total click-to-feedback | < 100ms | 200ms |

### Network Targets

| Scenario | Assumption |
|----------|------------|
| 3G connection | 1.5 Mbps, 300ms RTT |
| 4G connection | 10 Mbps, 100ms RTT |
| WiFi | 50 Mbps, 20ms RTT |

Must be usable on 3G.

### Asset Loading Priority

```
Critical (blocking):
  1. Minimal CSS for above-fold
  2. Core JavaScript (auth, API client)
  3. Countdown timer logic

High Priority:
  4. Product images (above fold)
  5. Full CSS

Low Priority:
  6. Analytics
  7. Below-fold images
  8. Optional features
```

---

## State Management Patterns

### State Categories

```
┌─────────────────────────────────────────────────────┐
│                   APPLICATION STATE                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Server    │  │   Client    │  │    UI       │ │
│  │   State     │  │   State     │  │   State     │ │
│  │             │  │             │  │             │ │
│  │ • Products  │  │ • Cart      │  │ • Modals    │ │
│  │ • Orders    │  │ • Drafts    │  │ • Loading   │ │
│  │ • User      │  │ • Prefs     │  │ • Errors    │ │
│  │ • Stock     │  │             │  │ • Focus     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│        ▲                                            │
│        │ sync                                       │
│        ▼                                            │
│  ┌─────────────┐                                   │
│  │   Cache     │                                   │
│  │   Layer     │                                   │
│  └─────────────┘                                   │
└─────────────────────────────────────────────────────┘
```

### Server State Rules

- **Single source of truth**: Server, not client
- **Cache invalidation**: On mutation, invalidate related queries
- **Optimistic updates**: Show success, rollback on error
- **Stale-while-revalidate**: Show cached, fetch fresh in background

### Order Placement State Machine

```
IDLE
  │
  ▼ user clicks "Buy"
VALIDATING
  │
  ├─ validation fails → IDLE (show error)
  │
  ▼ validation passes
SUBMITTING
  │
  ├─ network error → RETRY_PENDING
  ├─ 409 OUT_OF_STOCK → FAILED
  ├─ 4xx error → FAILED
  │
  ▼ 201 created
PENDING_PAYMENT
  │
  ├─ redirect to payment
  │
  ▼ payment completed (webhook via WebSocket)
CONFIRMED
  │
  ▼
COMPLETE
```

### Optimistic Update Rules

```
✅ Use optimistic updates for:
   - Adding to cart
   - Updating quantities
   - Form input feedback

❌ Never use optimistic updates for:
   - Order placement (must confirm with server)
   - Payment status
   - Stock availability
```

---

## Testing Requirements

### Test Categories

| Category | Purpose | When |
|----------|---------|------|
| Unit | Component logic | Every commit |
| Integration | API contract | Every PR |
| E2E | Critical flows | Daily |
| Load | Concurrency | Pre-release |
| Visual | UI regression | Every PR |

### Critical User Journeys

Must have E2E coverage:

```
1. Registration → Login → View Product
2. Login → Wait for Sale → Place Order → Payment
3. Login → View Orders → Cancel Order
4. Failed Payment → Return → Retry
5. Sale Sold Out → Error Display
```

### API Contract Tests

Every endpoint must have:

```
- Success case (200/201)
- Validation error (400)
- Authentication error (401)
- Business logic error (409)
- Server error handling (500)
```

### Load Testing Scenarios

```
Scenario: Flash Sale Surge
  - Ramp: 0 → 10,000 users over 10 seconds
  - Sustain: 10,000 concurrent for 60 seconds
  - Target: < 200ms P95 response time
  - Target: < 1% error rate

Scenario: Sustained Traffic
  - Users: 1,000 concurrent
  - Duration: 1 hour
  - Target: < 100ms P50 response time
  - Target: 0% error rate
```

### Chaos Testing

Frontend must handle:

```
- API returns 500 for 30 seconds
- WebSocket drops every 10 seconds
- API latency increases to 5 seconds
- Backend returns malformed JSON
- Clock skew of ±30 seconds
```

---

## Appendix: API Endpoint Details

### POST /orders

**Request:**
```http
POST /v1/orders
Authorization: Bearer <token>
X-Idempotency-Key: <uuid>
Content-Type: application/json

{
  "product_id": "uuid",
  "quantity": 1
}
```

**Success Response (201):**
```json
{
  "data": {
    "order_id": "uuid",
    "status": "pending",
    "payment_url": "https://checkout.razorpay.com/...",
    "expires_at": "2024-01-15T10:15:00Z"
  }
}
```

**Error Responses:**

| Status | Code | When |
|--------|------|------|
| 400 | INVALID_INPUT | Bad request body |
| 401 | TOKEN_EXPIRED | JWT expired |
| 409 | OUT_OF_STOCK | No stock |
| 409 | SALE_NOT_STARTED | Too early |
| 409 | SALE_ENDED | Too late |
| 409 | PURCHASE_LIMIT_EXCEEDED | User bought max |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |

### GET /products/{id}/stock

**Request:**
```http
GET /v1/products/uuid/stock
```

**Response (200):**
```json
{
  "data": {
    "product_id": "uuid",
    "available": 45,
    "reserved": 10,
    "status": "in_stock",
    "updated_at": "2024-01-15T10:00:00.123Z"
  }
}
```

**Status Values:**
- `in_stock` - Available for purchase
- `low_stock` - Less than threshold
- `sold_out` - Zero available
- `not_for_sale` - Sale not active

---

> **Next Steps**: When framework is chosen, create framework-specific implementation guide based on these specifications.
