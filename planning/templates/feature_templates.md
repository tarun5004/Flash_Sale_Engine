# Feature Implementation Templates

> **Purpose**: Ready-to-use code templates for implementing Flash Sale Engine features.  
> **Usage**: Copy the relevant template, paste into the correct file, then implement the logic.  
> **Status**: Templates only - no business logic included.

---

## Table of Contents

1. [Services](#services)
   - [OrderService](#orderservice)
   - [StockService](#stockservice)
   - [PaymentService](#paymentservice)
   - [UserService](#userservice)
2. [Routers](#routers)
   - [Orders Router](#orders-router)
   - [Auth Router](#auth-router)
   - [Webhooks Router](#webhooks-router)
3. [Core Modules](#core-modules)
   - [Dependencies](#dependencies)
   - [Cache](#cache)
   - [Rate Limiter](#rate-limiter)
4. [Schemas](#schemas)
   - [Order Schemas (Extended)](#order-schemas-extended)
   - [Auth Schemas](#auth-schemas)

---

# Services

## OrderService

**File**: `app/services/order_service.py`

```python
"""
Order Service - Flash Sale Engine
==================================

PURPOSE:
    Core flash sale order placement logic.
    Handles the critical path: user clicks "Buy" → order confirmed.

RESPONSIBILITIES:
    - Validate order request
    - Check stock availability
    - Reserve stock atomically
    - Create order record
    - Integrate with payment
    - Handle order state transitions

DOES NOT:
    - Directly manipulate product stock (StockService does that)
    - Process payments (PaymentService does that)
    - Handle HTTP concerns (routers do that)
    - Send notifications (future NotificationService)

TRANSACTION BOUNDARIES:
    - place_order: Single transaction for stock reservation + order creation
    - confirm_order: Separate transaction after payment success
    - fail_order: Must release reserved stock in same transaction

CRITICAL:
    This is the most important service in flash sale.
    Every method must be idempotent where possible.
    All failures must have clear rollback paths.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

# TODO: Import when implemented
# from app.models.order import Order, OrderStatus
# from app.repositories.order_repo import OrderRepository
# from app.repositories.product_repo import ProductRepository
# from app.services.stock_service import StockService
# from app.schemas.order_schema import OrderCreate, OrderResponse


class OrderService:
    """
    Flash sale order management service.
    
    Lifecycle:
        PENDING → CONFIRMED (payment success)
        PENDING → FAILED (payment failed / timeout)
        CONFIRMED → CANCELLED (user request within window)
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            session: SQLAlchemy async session (injected by FastAPI)
        """
        self.session = session
        # TODO: Initialize repositories
        # self.order_repo = OrderRepository(session)
        # self.product_repo = ProductRepository(session)
        # self.stock_service = StockService(session)
    
    # =========================================================================
    # PUBLIC METHODS
    # =========================================================================
    
    async def place_order(
        self,
        user_id: UUID,
        product_id: UUID,
        quantity: int,
        idempotency_key: str,
    ) -> dict:
        """
        Place a flash sale order.
        
        This is THE critical path. Must be:
        - Fast (< 100ms target)
        - Atomic (stock + order in one transaction)
        - Idempotent (same key = same result)
        
        Args:
            user_id: Authenticated user's ID
            product_id: Product to purchase
            quantity: Number of units
            idempotency_key: Client-provided unique key
            
        Returns:
            {
                "order_id": UUID,
                "status": "pending",
                "payment_url": "https://...",
                "expires_at": datetime,
            }
            
        Raises:
            OutOfStockError: No stock available
            InvalidQuantityError: Exceeds per-user limit
            ProductNotFoundError: Product doesn't exist
            SaleNotActiveError: Flash sale not started/ended
        
        Flow:
            1. Check idempotency (return existing if found)
            2. Validate product exists and sale is active
            3. Check per-user purchase limit
            4. Reserve stock (StockService.reserve_stock)
            5. Create order with PENDING status
            6. Generate payment session
            7. Return payment URL
        """
        raise NotImplementedError("place_order not implemented")
    
    async def confirm_order(self, order_id: UUID, payment_id: str) -> dict:
        """
        Confirm order after successful payment.
        
        Called by payment webhook handler.
        
        Args:
            order_id: Order to confirm
            payment_id: Payment gateway's payment ID
            
        Returns:
            {"order_id": UUID, "status": "confirmed"}
            
        Raises:
            OrderNotFoundError: Order doesn't exist
            InvalidOrderStateError: Order not in PENDING state
        
        Flow:
            1. Load order with FOR UPDATE lock
            2. Verify current state is PENDING
            3. Update status to CONFIRMED
            4. Store payment_id
            5. Commit transaction
        """
        raise NotImplementedError("confirm_order not implemented")
    
    async def fail_order(self, order_id: UUID, reason: str) -> dict:
        """
        Mark order as failed and release stock.
        
        Called when:
        - Payment fails
        - Payment times out
        - User abandons checkout
        
        Args:
            order_id: Order to fail
            reason: Failure reason for logging
            
        Returns:
            {"order_id": UUID, "status": "failed", "stock_released": True}
            
        CRITICAL:
            Must release reserved stock in the same transaction.
            If stock release fails, order must NOT be marked failed.
        """
        raise NotImplementedError("fail_order not implemented")
    
    async def cancel_order(self, order_id: UUID, user_id: UUID) -> dict:
        """
        Cancel a confirmed order (user-initiated).
        
        Args:
            order_id: Order to cancel
            user_id: Must match order owner
            
        Returns:
            {"order_id": UUID, "status": "cancelled", "refund_initiated": True}
            
        Raises:
            OrderNotFoundError: Order doesn't exist
            UnauthorizedError: user_id doesn't match order owner
            CancellationWindowClosedError: Too late to cancel
            
        Business Rules:
            - Only CONFIRMED orders can be cancelled
            - Cancellation window: 24 hours from confirmation
            - Must initiate refund process
        """
        raise NotImplementedError("cancel_order not implemented")
    
    async def get_order(self, order_id: UUID, user_id: UUID) -> dict:
        """
        Get order details.
        
        Args:
            order_id: Order to retrieve
            user_id: Must match order owner
            
        Returns:
            Full order details including status, items, payment info
            
        Raises:
            OrderNotFoundError: Order doesn't exist
            UnauthorizedError: user_id doesn't match
        """
        raise NotImplementedError("get_order not implemented")
    
    async def get_user_orders(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """
        Get paginated list of user's orders.
        
        Args:
            user_id: User whose orders to retrieve
            status: Optional filter by status
            limit: Max results (default 20, max 100)
            offset: Pagination offset
            
        Returns:
            {
                "orders": [...],
                "total": int,
                "limit": int,
                "offset": int,
            }
        """
        raise NotImplementedError("get_user_orders not implemented")
    
    async def expire_pending_orders(self, older_than_minutes: int = 15) -> int:
        """
        Background job: Expire old pending orders.
        
        Args:
            older_than_minutes: Orders older than this are expired
            
        Returns:
            Number of orders expired
            
        Called by:
            Celery beat scheduler every 5 minutes
            
        Flow:
            1. Find all PENDING orders older than threshold
            2. For each order:
               a. Release reserved stock
               b. Mark as EXPIRED
            3. Return count
        """
        raise NotImplementedError("expire_pending_orders not implemented")
    
    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================
    
    async def _check_idempotency(self, idempotency_key: str) -> Optional[dict]:
        """
        Check if order with this idempotency key exists.
        
        Returns:
            Existing order response if found, None otherwise
        """
        raise NotImplementedError("_check_idempotency not implemented")
    
    async def _validate_purchase_limit(
        self,
        user_id: UUID,
        product_id: UUID,
        quantity: int,
    ) -> None:
        """
        Check if user is within per-product purchase limit.
        
        Raises:
            PurchaseLimitExceededError: If limit exceeded
        """
        raise NotImplementedError("_validate_purchase_limit not implemented")
    
    async def _validate_sale_active(self, product_id: UUID) -> None:
        """
        Check if flash sale is currently active for product.
        
        Raises:
            SaleNotActiveError: If sale hasn't started or has ended
        """
        raise NotImplementedError("_validate_sale_active not implemented")
    
    async def _create_order_record(
        self,
        user_id: UUID,
        product_id: UUID,
        quantity: int,
        unit_price: float,
        idempotency_key: str,
    ) -> "Order":
        """
        Create order record in database.
        
        Returns:
            Created Order model instance
        """
        raise NotImplementedError("_create_order_record not implemented")
```

---

## StockService

**File**: `app/services/stock_service.py`

```python
"""
Stock Service - Flash Sale Engine
==================================

PURPOSE:
    Dedicated service for inventory operations.
    Handles atomic stock reservation and release.

RESPONSIBILITIES:
    - Reserve stock atomically
    - Release reserved stock
    - Check real-time availability
    - Prevent overselling

DOES NOT:
    - Handle order logic (OrderService does that)
    - Manage product data (ProductService does that)
    - Cache stock counts (future CacheService)

CRITICAL PATTERNS:
    1. SELECT FOR UPDATE on every stock modification
    2. Single-row updates only (no bulk without locks)
    3. Always verify sufficient stock before decrement
    4. Release must be idempotent

WHY SEPARATE SERVICE:
    Stock operations need isolation because:
    - Different transaction boundaries than orders
    - Will need Redis layer in future
    - Easier to add distributed locking later
    - Can be replaced with external inventory system
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

# TODO: Import when implemented
# from app.repositories.product_repo import ProductRepository
# from app.models.product import Product


class StockError(Exception):
    """Base exception for stock operations."""
    pass


class InsufficientStockError(StockError):
    """Raised when requested quantity exceeds available stock."""
    def __init__(self, product_id: UUID, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for {product_id}: "
            f"requested {requested}, available {available}"
        )


class StockService:
    """
    Inventory management service.
    
    All methods use database-level locking to prevent race conditions.
    Future: Will add Redis-based distributed locking.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        # TODO: Initialize repository
        # self.product_repo = ProductRepository(session)
    
    # =========================================================================
    # PUBLIC METHODS
    # =========================================================================
    
    async def reserve_stock(
        self,
        product_id: UUID,
        quantity: int,
        reservation_id: Optional[str] = None,
    ) -> dict:
        """
        Reserve stock for an order.
        
        Uses SELECT FOR UPDATE to prevent race conditions.
        
        Args:
            product_id: Product to reserve
            quantity: Units to reserve
            reservation_id: Optional ID for tracking (order_id)
            
        Returns:
            {
                "success": True,
                "reserved": quantity,
                "remaining": available_after,
            }
            
        Raises:
            InsufficientStockError: Not enough stock
            ProductNotFoundError: Product doesn't exist
            
        SQL Pattern:
            BEGIN;
            SELECT stock FROM products WHERE id = ? FOR UPDATE;
            -- Check if stock >= quantity
            UPDATE products SET stock = stock - ? WHERE id = ?;
            COMMIT;
        """
        raise NotImplementedError("reserve_stock not implemented")
    
    async def release_stock(
        self,
        product_id: UUID,
        quantity: int,
        reservation_id: Optional[str] = None,
    ) -> dict:
        """
        Release previously reserved stock.
        
        Called when:
        - Order fails
        - Order expires
        - Order cancelled
        
        Args:
            product_id: Product to release
            quantity: Units to release
            reservation_id: Should match original reservation
            
        Returns:
            {"success": True, "released": quantity, "new_stock": updated_count}
            
        MUST BE IDEMPOTENT:
            If called twice with same reservation_id, second call is no-op.
            
        Note:
            Uses optimistic approach - adds back to stock.
            Future: Track reservations separately for audit.
        """
        raise NotImplementedError("release_stock not implemented")
    
    async def get_available_stock(self, product_id: UUID) -> int:
        """
        Get current available stock for product.
        
        Args:
            product_id: Product to check
            
        Returns:
            Available stock count
            
        Note:
            This is a point-in-time read. Stock may change
            immediately after this call. Use reserve_stock
            for actual reservation.
            
        Use cases:
            - Display stock on product page
            - Check before showing "Add to Cart"
            - Admin dashboard
        """
        raise NotImplementedError("get_available_stock not implemented")
    
    async def atomic_decrement(
        self,
        product_id: UUID,
        quantity: int,
    ) -> bool:
        """
        Atomically decrement stock if sufficient.
        
        Single SQL statement, no separate SELECT:
        
            UPDATE products 
            SET stock = stock - :qty 
            WHERE id = :id AND stock >= :qty
        
        Args:
            product_id: Product to decrement
            quantity: Amount to decrement
            
        Returns:
            True if decrement succeeded, False if insufficient stock
            
        Use case:
            Ultra-high performance path where you just need
            yes/no without detailed error handling.
        """
        raise NotImplementedError("atomic_decrement not implemented")
    
    async def check_and_reserve_batch(
        self,
        items: list[dict],
    ) -> dict:
        """
        Reserve stock for multiple products atomically.
        
        Args:
            items: [{"product_id": UUID, "quantity": int}, ...]
            
        Returns:
            {
                "success": True/False,
                "reserved": [...],  # Successfully reserved
                "failed": [...],    # Failed items with reasons
            }
            
        ATOMICITY:
            If any item fails, ALL reservations are rolled back.
            This is all-or-nothing.
            
        Use case:
            Cart checkout with multiple items.
        """
        raise NotImplementedError("check_and_reserve_batch not implemented")
    
    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================
    
    async def _lock_product_row(self, product_id: UUID) -> "Product":
        """
        Acquire row-level lock on product.
        
        Uses SELECT ... FOR UPDATE.
        
        Returns:
            Locked Product instance
            
        Raises:
            ProductNotFoundError: If product doesn't exist
        """
        raise NotImplementedError("_lock_product_row not implemented")
    
    async def _log_stock_movement(
        self,
        product_id: UUID,
        quantity: int,
        movement_type: str,
        reference_id: Optional[str] = None,
    ) -> None:
        """
        Log stock movement for audit trail.
        
        Future: Write to separate stock_movements table.
        
        Args:
            product_id: Affected product
            quantity: Positive = increase, negative = decrease
            movement_type: "reservation", "release", "sale", "restock"
            reference_id: Order ID or other reference
        """
        raise NotImplementedError("_log_stock_movement not implemented")
```

---

## PaymentService

**File**: `app/services/payment_service.py`

```python
"""
Payment Service - Flash Sale Engine
====================================

PURPOSE:
    Integration layer with external payment gateways.
    Handles payment session creation, verification, and webhooks.

RESPONSIBILITIES:
    - Create payment sessions with gateway
    - Verify webhook signatures
    - Process payment status updates
    - Handle refunds

DOES NOT:
    - Store full payment details (PCI compliance)
    - Handle order state (OrderService does that)
    - Decide business rules (caller decides)

SUPPORTED GATEWAYS:
    - Razorpay (primary for India)
    - Stripe (international)

SECURITY:
    - Never log full card details
    - Verify webhook signatures before processing
    - Use idempotency keys with gateway

ARCHITECTURE:
    Uses Strategy pattern internally:
    - PaymentService.create_session() delegates to
    - RazorpayProvider.create_session() or
    - StripeProvider.create_session()
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

# TODO: Import when implemented
# from app.models.payment import Payment
# from app.repositories.payment_repo import PaymentRepository


class PaymentError(Exception):
    """Base exception for payment operations."""
    pass


class PaymentGatewayError(PaymentError):
    """Raised when gateway returns an error."""
    def __init__(self, gateway: str, code: str, message: str):
        self.gateway = gateway
        self.code = code
        self.message = message
        super().__init__(f"{gateway} error [{code}]: {message}")


class PaymentSignatureError(PaymentError):
    """Raised when webhook signature verification fails."""
    pass


class PaymentService:
    """
    Payment gateway integration service.
    
    Abstracts away specific gateway implementation.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        # TODO: Initialize repository and gateway clients
        # self.payment_repo = PaymentRepository(session)
        # self.razorpay_client = razorpay.Client(...)
        # self.stripe_client = stripe
    
    # =========================================================================
    # PUBLIC METHODS - SESSION CREATION
    # =========================================================================
    
    async def create_payment_session(
        self,
        order_id: UUID,
        amount: float,
        currency: str = "INR",
        customer_email: str = None,
        customer_phone: str = None,
        provider: str = "razorpay",
    ) -> dict:
        """
        Create a payment session with the gateway.
        
        Args:
            order_id: Our internal order ID
            amount: Amount in major units (e.g., 100.00 for ₹100)
            currency: ISO currency code
            customer_email: For receipt
            customer_phone: For OTP (Razorpay)
            provider: "razorpay" or "stripe"
            
        Returns:
            {
                "session_id": "gateway_session_id",
                "payment_url": "https://checkout.razorpay.com/...",
                "expires_at": datetime,
                "provider": "razorpay",
            }
            
        Raises:
            PaymentGatewayError: Gateway returned error
            
        Note:
            Amount is converted to minor units internally
            (paise for INR, cents for USD)
        """
        raise NotImplementedError("create_payment_session not implemented")
    
    # =========================================================================
    # PUBLIC METHODS - WEBHOOK HANDLING
    # =========================================================================
    
    async def handle_webhook(
        self,
        provider: str,
        payload: dict,
        signature: str,
    ) -> dict:
        """
        Process webhook from payment gateway.
        
        Args:
            provider: "razorpay" or "stripe"
            payload: Parsed JSON body
            signature: Signature header value
            
        Returns:
            {
                "processed": True,
                "event_type": "payment.captured",
                "order_id": UUID,
                "payment_id": "pay_xxx",
            }
            
        Events handled:
            - payment.authorized (Razorpay)
            - payment.captured (Razorpay)
            - payment.failed (Razorpay)
            - payment_intent.succeeded (Stripe)
            - payment_intent.payment_failed (Stripe)
            
        CRITICAL:
            Must be idempotent - same webhook may arrive multiple times.
        """
        raise NotImplementedError("handle_webhook not implemented")
    
    async def verify_webhook_signature(
        self,
        provider: str,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify webhook signature from gateway.
        
        Args:
            provider: "razorpay" or "stripe"
            payload: Raw request body (bytes)
            signature: Signature header value
            
        Returns:
            True if signature is valid
            
        Raises:
            PaymentSignatureError: If verification fails
            
        Security:
            ALWAYS verify before processing any webhook.
        """
        raise NotImplementedError("verify_webhook_signature not implemented")
    
    # =========================================================================
    # PUBLIC METHODS - REFUNDS
    # =========================================================================
    
    async def initiate_refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: str = "customer_request",
    ) -> dict:
        """
        Initiate refund for a payment.
        
        Args:
            payment_id: Gateway's payment ID
            amount: Partial refund amount (None = full refund)
            reason: Refund reason for records
            
        Returns:
            {
                "refund_id": "rfnd_xxx",
                "status": "pending",
                "amount": float,
            }
            
        Note:
            Refund is async - status updates come via webhook.
        """
        raise NotImplementedError("initiate_refund not implemented")
    
    async def get_refund_status(self, refund_id: str) -> dict:
        """
        Get current status of a refund.
        
        Args:
            refund_id: Gateway's refund ID
            
        Returns:
            {
                "refund_id": "rfnd_xxx",
                "status": "processed" | "pending" | "failed",
                "amount": float,
            }
        """
        raise NotImplementedError("get_refund_status not implemented")
    
    # =========================================================================
    # PUBLIC METHODS - QUERIES
    # =========================================================================
    
    async def get_payment_status(self, payment_id: str) -> dict:
        """
        Get current payment status from gateway.
        
        Args:
            payment_id: Gateway's payment ID
            
        Returns:
            {
                "payment_id": "pay_xxx",
                "status": "captured" | "failed" | "pending",
                "amount": float,
                "method": "card" | "upi" | "netbanking",
            }
            
        Use case:
            Reconciliation, customer support queries
        """
        raise NotImplementedError("get_payment_status not implemented")
    
    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================
    
    async def _create_razorpay_order(
        self,
        amount_paise: int,
        currency: str,
        receipt: str,
    ) -> dict:
        """Create Razorpay order."""
        raise NotImplementedError("_create_razorpay_order not implemented")
    
    async def _create_stripe_session(
        self,
        amount_cents: int,
        currency: str,
        order_id: str,
    ) -> dict:
        """Create Stripe checkout session."""
        raise NotImplementedError("_create_stripe_session not implemented")
    
    async def _record_payment(
        self,
        order_id: UUID,
        provider: str,
        session_id: str,
        amount: float,
    ) -> "Payment":
        """Record payment attempt in database."""
        raise NotImplementedError("_record_payment not implemented")
    
    async def _update_payment_status(
        self,
        payment_id: str,
        status: str,
        gateway_response: dict,
    ) -> None:
        """Update payment record with gateway response."""
        raise NotImplementedError("_update_payment_status not implemented")
```

---

## UserService

**File**: `app/services/user_service.py`

```python
"""
User Service - Flash Sale Engine
=================================

PURPOSE:
    User account management and authentication.
    Handles registration, login, and profile operations.

RESPONSIBILITIES:
    - User registration with validation
    - Password hashing and verification
    - JWT token generation
    - Profile management

DOES NOT:
    - Handle HTTP concerns (routers do that)
    - Manage sessions (JWT is stateless)
    - Authorize actions (dependencies do that)

SECURITY:
    - Passwords hashed with bcrypt
    - JWTs signed with HS256
    - Rate limiting on login (via middleware)
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

# TODO: Import when implemented
# from app.models.user import User
# from app.repositories.user_repo import UserRepository
# from app.core.config import settings
# from app.security import hash_password, verify_password, create_access_token


class UserError(Exception):
    """Base exception for user operations."""
    pass


class UserExistsError(UserError):
    """Raised when email already registered."""
    pass


class InvalidCredentialsError(UserError):
    """Raised when login credentials are invalid."""
    pass


class UserNotFoundError(UserError):
    """Raised when user doesn't exist."""
    pass


class UserService:
    """
    User management service.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        # TODO: Initialize repository
        # self.user_repo = UserRepository(session)
    
    # =========================================================================
    # PUBLIC METHODS - AUTHENTICATION
    # =========================================================================
    
    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None,
    ) -> dict:
        """
        Register new user.
        
        Args:
            email: User's email (must be unique)
            password: Plain text password (will be hashed)
            full_name: Display name
            phone: Optional phone number
            
        Returns:
            {
                "user_id": UUID,
                "email": str,
                "full_name": str,
                "created_at": datetime,
            }
            
        Raises:
            UserExistsError: Email already registered
            
        Validation:
            - Email format validation
            - Password strength (min 8 chars, 1 number, 1 special)
            - Phone format (if provided)
        """
        raise NotImplementedError("register not implemented")
    
    async def login(
        self,
        email: str,
        password: str,
    ) -> dict:
        """
        Authenticate user and return tokens.
        
        Args:
            email: User's email
            password: Plain text password
            
        Returns:
            {
                "access_token": str,
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": UUID,
                    "email": str,
                    "full_name": str,
                }
            }
            
        Raises:
            InvalidCredentialsError: Wrong email or password
            
        Security:
            - Same error for wrong email and wrong password
            - Rate limited by middleware
        """
        raise NotImplementedError("login not implemented")
    
    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Issue new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            {
                "access_token": str,
                "token_type": "bearer",
                "expires_in": 3600,
            }
            
        Raises:
            InvalidTokenError: Token invalid or expired
        """
        raise NotImplementedError("refresh_token not implemented")
    
    # =========================================================================
    # PUBLIC METHODS - PROFILE
    # =========================================================================
    
    async def get_profile(self, user_id: UUID) -> dict:
        """
        Get user profile.
        
        Args:
            user_id: User's ID
            
        Returns:
            User profile data (excludes password hash)
            
        Raises:
            UserNotFoundError: User doesn't exist
        """
        raise NotImplementedError("get_profile not implemented")
    
    async def update_profile(
        self,
        user_id: UUID,
        updates: dict,
    ) -> dict:
        """
        Update user profile.
        
        Args:
            user_id: User's ID
            updates: Fields to update (validated by schema)
            
        Returns:
            Updated profile
            
        Allowed updates:
            - full_name
            - phone
            - address
            
        Not allowed:
            - email (requires verification flow)
            - password (requires change_password)
        """
        raise NotImplementedError("update_profile not implemented")
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> dict:
        """
        Change user password.
        
        Args:
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            {"success": True, "message": "Password changed"}
            
        Raises:
            InvalidCredentialsError: Current password wrong
        """
        raise NotImplementedError("change_password not implemented")
    
    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        raise NotImplementedError("_hash_password not implemented")
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        raise NotImplementedError("_verify_password not implemented")
    
    def _create_access_token(
        self,
        user_id: UUID,
        expires_delta: timedelta = None,
    ) -> str:
        """Generate JWT access token."""
        raise NotImplementedError("_create_access_token not implemented")
    
    def _validate_password_strength(self, password: str) -> None:
        """
        Validate password meets requirements.
        
        Raises:
            WeakPasswordError: If requirements not met
        """
        raise NotImplementedError("_validate_password_strength not implemented")
```

---

# Routers

## Orders Router

**File**: `app/routers/orders.py`

```python
"""
Orders Router - Flash Sale Engine
==================================

PURPOSE:
    HTTP endpoint definitions for order operations.
    Handles request/response, delegates to OrderService.

RESPONSIBILITIES:
    - Request validation (via Pydantic schemas)
    - Authentication (via dependencies)
    - Response formatting
    - Error translation to HTTP status codes

DOES NOT:
    - Contain business logic (OrderService does that)
    - Access database directly (repositories do that)
    - Handle transactions (services do that)

AUTHENTICATION:
    All endpoints require valid JWT token.
    Token is validated by get_current_user dependency.

IDEMPOTENCY:
    POST /orders requires X-Idempotency-Key header.
    Same key + same request = same response.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
from uuid import UUID

# TODO: Import when implemented
# from app.services.order_service import OrderService
# from app.schemas.order_schema import OrderCreate, OrderResponse, OrderListResponse
# from app.core.dependencies import get_current_user, get_db


router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


# =============================================================================
# ORDER CREATION
# =============================================================================

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Place a flash sale order",
    description="""
    Place an order for a flash sale product.
    
    **Requirements:**
    - Valid authentication token
    - Product must have active flash sale
    - Sufficient stock available
    - Within per-user purchase limit
    
    **Idempotency:**
    Include `X-Idempotency-Key` header. If same key is used again,
    the original order response will be returned.
    """,
    responses={
        201: {"description": "Order placed successfully"},
        400: {"description": "Invalid request"},
        401: {"description": "Not authenticated"},
        409: {"description": "Out of stock or limit exceeded"},
    },
)
async def create_order(
    # order_data: OrderCreate,
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key"),
    # current_user = Depends(get_current_user),
    # db = Depends(get_db),
):
    """
    Create a new order.
    
    Flow:
        1. Validate request
        2. Check authentication
        3. Delegate to OrderService.place_order()
        4. Return order details with payment URL
    """
    # TODO: Implement when dependencies are ready
    # service = OrderService(db)
    # result = await service.place_order(
    #     user_id=current_user.id,
    #     product_id=order_data.product_id,
    #     quantity=order_data.quantity,
    #     idempotency_key=x_idempotency_key,
    # )
    # return result
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Order creation not implemented yet",
    )


# =============================================================================
# ORDER RETRIEVAL
# =============================================================================

@router.get(
    "/",
    summary="Get user's orders",
    description="Get paginated list of current user's orders.",
)
async def list_orders(
    status_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    # current_user = Depends(get_current_user),
    # db = Depends(get_db),
):
    """
    List orders for authenticated user.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Order listing not implemented yet",
    )


@router.get(
    "/{order_id}",
    summary="Get order details",
    description="Get details of a specific order.",
)
async def get_order(
    order_id: UUID,
    # current_user = Depends(get_current_user),
    # db = Depends(get_db),
):
    """
    Get single order by ID.
    
    User can only access their own orders.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Order retrieval not implemented yet",
    )


# =============================================================================
# ORDER ACTIONS
# =============================================================================

@router.post(
    "/{order_id}/cancel",
    summary="Cancel order",
    description="""
    Cancel a confirmed order.
    
    Only available within 24 hours of order confirmation.
    Refund will be initiated automatically.
    """,
)
async def cancel_order(
    order_id: UUID,
    # current_user = Depends(get_current_user),
    # db = Depends(get_db),
):
    """
    Cancel an order.
    
    Flow:
        1. Verify order belongs to user
        2. Check cancellation window
        3. Delegate to OrderService.cancel_order()
        4. Return cancellation confirmation
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Order cancellation not implemented yet",
    )
```

---

## Auth Router

**File**: `app/routers/auth.py`

```python
"""
Auth Router - Flash Sale Engine
================================

PURPOSE:
    HTTP endpoints for authentication.
    Handles registration, login, and token operations.

RESPONSIBILITIES:
    - Request validation
    - Response formatting
    - Rate limiting integration
    - Token management

DOES NOT:
    - Handle password hashing (UserService does that)
    - Store sessions (JWT is stateless)
    - Implement auth logic (UserService does that)

RATE LIMITING:
    - /register: 5 per minute per IP
    - /login: 10 per minute per IP
    - /refresh: 30 per minute per user
"""

from fastapi import APIRouter, HTTPException, status, Depends

# TODO: Import when implemented
# from app.services.user_service import UserService
# from app.schemas.user_schema import (
#     UserRegister, 
#     UserLogin, 
#     TokenResponse,
#     UserResponse,
# )
# from app.core.dependencies import get_db


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


# =============================================================================
# REGISTRATION
# =============================================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="""
    Create a new user account.
    
    **Validation:**
    - Email must be valid format and unique
    - Password min 8 chars with 1 number and 1 special character
    - Phone number format validated (if provided)
    """,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Validation error"},
        409: {"description": "Email already registered"},
    },
)
async def register(
    # user_data: UserRegister,
    # db = Depends(get_db),
):
    """
    Register new user.
    
    Flow:
        1. Validate request data
        2. Check email uniqueness
        3. Hash password
        4. Create user record
        5. Return user data (no token - must login)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Registration not implemented yet",
    )


# =============================================================================
# LOGIN
# =============================================================================

@router.post(
    "/login",
    summary="User login",
    description="""
    Authenticate user and get access token.
    
    Returns JWT access token valid for 1 hour.
    Include token in Authorization header: `Bearer <token>`
    """,
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        429: {"description": "Too many attempts"},
    },
)
async def login(
    # credentials: UserLogin,
    # db = Depends(get_db),
):
    """
    Login user.
    
    Flow:
        1. Find user by email
        2. Verify password
        3. Generate JWT token
        4. Return token and user info
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login not implemented yet",
    )


# =============================================================================
# TOKEN REFRESH
# =============================================================================

@router.post(
    "/refresh",
    summary="Refresh access token",
    description="Get new access token using refresh token.",
)
async def refresh_token(
    # refresh_data: RefreshTokenRequest,
):
    """
    Refresh access token.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not implemented yet",
    )


# =============================================================================
# CURRENT USER
# =============================================================================

@router.get(
    "/me",
    summary="Get current user",
    description="Get profile of authenticated user.",
)
async def get_current_user_profile(
    # current_user = Depends(get_current_user),
):
    """
    Get current user profile.
    
    Requires valid access token.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Profile retrieval not implemented yet",
    )
```

---

## Webhooks Router

**File**: `app/routers/webhooks.py`

```python
"""
Webhooks Router - Flash Sale Engine
====================================

PURPOSE:
    HTTP endpoint definitions for external webhook callbacks.
    Handles payment gateway notifications.

RESPONSIBILITIES:
    - Receive webhook POST requests from payment gateways
    - Extract signature headers for verification
    - Delegate processing to PaymentService
    - Return acknowledgment quickly
    - Handle errors gracefully (don't expose internals)

DOES NOT:
    - Verify signatures (PaymentService does that)
    - Process business logic (services do that)
    - Block on slow operations (use background tasks)

CRITICAL REQUIREMENTS:
    1. ALWAYS return 200 on successful processing
    2. Return 200 even if already processed (idempotency)
    3. Return 401 ONLY on signature failure
    4. Complete within gateway timeout (~30 seconds)
    5. Log ALL webhook payloads for debugging

SECURITY:
    - No authentication (gateways can't authenticate)
    - Signature verification is the security layer
    - Don't trust payload until signature verified
"""

from fastapi import APIRouter, Request, HTTPException, status, Header

# TODO: Import when implemented
# from app.services.payment_service import PaymentService, PaymentSignatureError


router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


# =============================================================================
# RAZORPAY WEBHOOK
# =============================================================================

@router.post(
    "/razorpay",
    status_code=status.HTTP_200_OK,
    summary="Razorpay payment webhook",
    description="""
    Receives payment status updates from Razorpay.
    
    Razorpay sends webhooks for:
    - payment.authorized
    - payment.captured
    - payment.failed
    - refund.created
    
    Signature verification uses X-Razorpay-Signature header.
    """,
    include_in_schema=False,  # Hide from public docs
)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature"),
):
    """
    Handle Razorpay webhook.
    
    Flow:
        1. Read raw body (needed for signature verification)
        2. Verify signature
        3. Parse JSON payload
        4. Process payment event
        5. Return acknowledgment
    """
    # TODO: Implement when PaymentService is ready
    return {
        "status": "ok",
        "message": "Webhook endpoint ready, processing not implemented",
    }


# =============================================================================
# STRIPE WEBHOOK
# =============================================================================

@router.post(
    "/stripe",
    status_code=status.HTTP_200_OK,
    summary="Stripe payment webhook",
    include_in_schema=False,
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook.
    """
    # TODO: Implement when PaymentService is ready
    return {
        "status": "ok",
        "message": "Stripe webhook endpoint ready, processing not implemented",
    }


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get(
    "/health",
    summary="Webhook endpoint health check",
)
async def webhook_health():
    """Health check for webhook endpoints."""
    return {"status": "healthy"}
```

---

# Core Modules

## Dependencies

**File**: `app/core/dependencies.py`

```python
"""
FastAPI Dependencies - Flash Sale Engine
=========================================

PURPOSE:
    Reusable dependency injection for endpoints.
    Provides authentication, database session, and services.

RESPONSIBILITIES:
    - Extract and validate JWT tokens
    - Provide database sessions
    - Inject service instances
    - Handle authorization

DOES NOT:
    - Contain business logic
    - Make database queries directly
    - Handle HTTP responses

USAGE:
    @router.get("/protected")
    async def protected_endpoint(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        ...
"""

from typing import Generator, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

# TODO: Import when implemented
# from app.db.session import async_session
# from app.models.user import User
# from app.repositories.user_repo import UserRepository
# from app.security import decode_token
# from app.core.config import settings


# Security scheme for OpenAPI docs
security = HTTPBearer()


# =============================================================================
# DATABASE SESSION
# =============================================================================

async def get_db() -> Generator[AsyncSession, None, None]:
    """
    Dependency for database session.
    
    Provides async session that auto-closes after request.
    
    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    # TODO: Implement when session is configured
    # async with async_session() as session:
    #     try:
    #         yield session
    #         await session.commit()
    #     except Exception:
    #         await session.rollback()
    #         raise
    #     finally:
    #         await session.close()
    raise NotImplementedError("get_db not implemented")


# =============================================================================
# AUTHENTICATION
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> "User":
    """
    Dependency for authenticated endpoints.
    
    Extracts JWT from Authorization header, validates it,
    and returns the User object.
    
    Raises:
        HTTPException 401: Token missing, invalid, or expired
        HTTPException 401: User not found
    
    Usage:
        @router.get("/me")
        async def get_profile(current_user: User = Depends(get_current_user)):
            return current_user
    """
    # TODO: Implement when security module is ready
    # token = credentials.credentials
    # try:
    #     payload = decode_token(token)
    #     user_id = UUID(payload["sub"])
    # except Exception:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid authentication credentials",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    # 
    # user_repo = UserRepository(db)
    # user = await user_repo.get_by_id(user_id)
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="User not found",
    #     )
    # 
    # return user
    raise NotImplementedError("get_current_user not implemented")


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional["User"]:
    """
    Dependency for optionally authenticated endpoints.
    
    Returns User if token present and valid, None otherwise.
    
    Usage:
        @router.get("/products")
        async def list_products(
            current_user: Optional[User] = Depends(get_current_user_optional)
        ):
            # Show personalized results if logged in
            ...
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# =============================================================================
# ADMIN AUTHORIZATION
# =============================================================================

async def get_admin_user(
    current_user: "User" = Depends(get_current_user),
) -> "User":
    """
    Dependency for admin-only endpoints.
    
    Raises:
        HTTPException 403: User is not admin
    
    Usage:
        @router.post("/products")
        async def create_product(admin: User = Depends(get_admin_user)):
            ...
    """
    # TODO: Implement when User model has is_admin field
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin access required",
    #     )
    # return current_user
    raise NotImplementedError("get_admin_user not implemented")


# =============================================================================
# SERVICE INJECTION
# =============================================================================

async def get_order_service(
    db: AsyncSession = Depends(get_db),
):
    """
    Dependency to inject OrderService.
    
    Usage:
        @router.post("/orders")
        async def create_order(
            service: OrderService = Depends(get_order_service)
        ):
            ...
    """
    # TODO: Import and return OrderService
    # from app.services.order_service import OrderService
    # return OrderService(db)
    raise NotImplementedError("get_order_service not implemented")


async def get_payment_service(
    db: AsyncSession = Depends(get_db),
):
    """Dependency to inject PaymentService."""
    # TODO: Import and return PaymentService
    raise NotImplementedError("get_payment_service not implemented")


async def get_user_service(
    db: AsyncSession = Depends(get_db),
):
    """Dependency to inject UserService."""
    # TODO: Import and return UserService
    raise NotImplementedError("get_user_service not implemented")
```

---

## Cache

**File**: `app/core/cache.py`

```python
"""
Cache Module - Flash Sale Engine
=================================

PURPOSE:
    Redis-based caching layer.
    Provides fast access to frequently read data.

RESPONSIBILITIES:
    - Cache product stock counts
    - Cache user session data
    - Cache rate limiter counters
    - Distributed lock support

DOES NOT:
    - Replace database (always fallback available)
    - Store sensitive data unencrypted
    - Handle business logic

PATTERNS:
    - Cache-aside (read-through not implemented yet)
    - TTL-based expiration
    - Distributed locking with Redlock

CONFIGURATION:
    - REDIS_URL from settings
    - Default TTL: 300 seconds (5 minutes)
    - Connection pooling: 10 connections
"""

from typing import Optional, Any
from datetime import timedelta
import json

# TODO: Import when implemented
# import redis.asyncio as redis
# from app.core.config import settings


class CacheError(Exception):
    """Base exception for cache operations."""
    pass


class Cache:
    """
    Redis cache wrapper.
    
    Provides high-level caching operations with
    automatic serialization and error handling.
    """
    
    def __init__(self, redis_client: Optional[Any] = None):
        """
        Initialize cache.
        
        Args:
            redis_client: Optional pre-configured Redis client
        """
        self._client = redis_client
        # TODO: Create client from settings if not provided
        # if not redis_client:
        #     self._client = redis.from_url(
        #         settings.REDIS_URL,
        #         encoding="utf-8",
        #         decode_responses=True,
        #     )
    
    # =========================================================================
    # BASIC OPERATIONS
    # =========================================================================
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized value or None if not found
        """
        # TODO: Implement
        # value = await self._client.get(key)
        # if value is None:
        #     return None
        # return json.loads(value)
        raise NotImplementedError("Cache.get not implemented")
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 5 minutes)
            
        Returns:
            True if set successfully
        """
        # TODO: Implement
        # serialized = json.dumps(value)
        # await self._client.setex(key, ttl, serialized)
        # return True
        raise NotImplementedError("Cache.set not implemented")
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if key didn't exist
        """
        # TODO: Implement
        # result = await self._client.delete(key)
        # return result > 0
        raise NotImplementedError("Cache.delete not implemented")
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        # TODO: Implement
        # return await self._client.exists(key) > 0
        raise NotImplementedError("Cache.exists not implemented")
    
    # =========================================================================
    # STOCK-SPECIFIC OPERATIONS
    # =========================================================================
    
    async def get_stock(self, product_id: str) -> Optional[int]:
        """
        Get cached stock count.
        
        Args:
            product_id: Product UUID as string
            
        Returns:
            Stock count or None if not cached
        """
        key = f"stock:{product_id}"
        # TODO: Implement
        raise NotImplementedError("Cache.get_stock not implemented")
    
    async def set_stock(
        self,
        product_id: str,
        stock: int,
        ttl: int = 60,
    ) -> bool:
        """
        Cache stock count.
        
        Shorter TTL (60s) because stock changes frequently.
        
        Args:
            product_id: Product UUID as string
            stock: Current stock count
            ttl: Time to live (default 60 seconds)
        """
        key = f"stock:{product_id}"
        # TODO: Implement
        raise NotImplementedError("Cache.set_stock not implemented")
    
    async def decrement_stock(
        self,
        product_id: str,
        amount: int = 1,
    ) -> Optional[int]:
        """
        Atomically decrement cached stock.
        
        Uses Redis DECRBY for atomicity.
        
        Args:
            product_id: Product UUID as string
            amount: Amount to decrement
            
        Returns:
            New stock value, or None if key doesn't exist
            
        Note:
            Does NOT check if stock goes negative.
            Use with database as source of truth.
        """
        key = f"stock:{product_id}"
        # TODO: Implement
        # if not await self.exists(key):
        #     return None
        # return await self._client.decrby(key, amount)
        raise NotImplementedError("Cache.decrement_stock not implemented")
    
    async def invalidate_stock(self, product_id: str) -> bool:
        """
        Invalidate cached stock (force re-read from DB).
        
        Args:
            product_id: Product UUID as string
        """
        key = f"stock:{product_id}"
        return await self.delete(key)
    
    # =========================================================================
    # DISTRIBUTED LOCKING
    # =========================================================================
    
    async def acquire_lock(
        self,
        lock_name: str,
        ttl: int = 10,
        retry_times: int = 3,
        retry_delay: float = 0.2,
    ) -> Optional[str]:
        """
        Acquire distributed lock.
        
        Args:
            lock_name: Unique lock identifier
            ttl: Lock expiry in seconds
            retry_times: Number of acquisition attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Lock token if acquired, None if failed
            
        Usage:
            token = await cache.acquire_lock("order:123")
            if token:
                try:
                    # Critical section
                    pass
                finally:
                    await cache.release_lock("order:123", token)
        """
        # TODO: Implement using SET NX EX pattern
        # import uuid
        # token = str(uuid.uuid4())
        # key = f"lock:{lock_name}"
        # 
        # for _ in range(retry_times):
        #     acquired = await self._client.set(
        #         key, token, nx=True, ex=ttl
        #     )
        #     if acquired:
        #         return token
        #     await asyncio.sleep(retry_delay)
        # 
        # return None
        raise NotImplementedError("Cache.acquire_lock not implemented")
    
    async def release_lock(self, lock_name: str, token: str) -> bool:
        """
        Release distributed lock.
        
        Only releases if token matches (prevents releasing others' locks).
        
        Args:
            lock_name: Lock identifier
            token: Token from acquire_lock
            
        Returns:
            True if released, False if token mismatch or lock expired
        """
        # TODO: Implement with Lua script for atomicity
        # key = f"lock:{lock_name}"
        # script = """
        # if redis.call("get", KEYS[1]) == ARGV[1] then
        #     return redis.call("del", KEYS[1])
        # else
        #     return 0
        # end
        # """
        # result = await self._client.eval(script, 1, key, token)
        # return result == 1
        raise NotImplementedError("Cache.release_lock not implemented")


# =============================================================================
# GLOBAL CACHE INSTANCE
# =============================================================================

# TODO: Initialize when settings are ready
# cache = Cache()

async def get_cache() -> Cache:
    """
    FastAPI dependency for cache access.
    
    Usage:
        @router.get("/product/{id}")
        async def get_product(
            id: UUID,
            cache: Cache = Depends(get_cache),
        ):
            cached = await cache.get(f"product:{id}")
            ...
    """
    # TODO: Return global cache instance
    # return cache
    raise NotImplementedError("get_cache not implemented")
```

---

## Rate Limiter

**File**: `app/core/rate_limiter.py`

```python
"""
Rate Limiter - Flash Sale Engine
=================================

PURPOSE:
    Protect endpoints from abuse and ensure fair access.
    Critical for flash sale where bots try to buy all stock.

RESPONSIBILITIES:
    - Track request counts per client
    - Block excessive requests
    - Provide fair queue during flash sales

DOES NOT:
    - Handle authentication (dependencies do that)
    - Log abuse attempts (logging middleware does that)
    - Make business decisions (just counts)

ALGORITHMS:
    - Fixed Window: Simple, some burstiness at window edges
    - Sliding Window: Smoother, more accurate
    - Token Bucket: Allows controlled bursts

STORAGE:
    Uses Redis for distributed rate limiting.
    Falls back to in-memory for single-instance dev.

CONFIGURATION:
    - Default limits in settings
    - Per-endpoint overrides possible
"""

from typing import Optional, Callable
from datetime import datetime
from fastapi import Request, HTTPException, status

# TODO: Import when implemented
# from app.core.cache import Cache, get_cache
# from app.core.config import settings


class RateLimitExceeded(HTTPException):
    """Exception when rate limit is exceeded."""
    
    def __init__(
        self,
        retry_after: int = 60,
        detail: str = "Rate limit exceeded",
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)},
        )


class RateLimiter:
    """
    Rate limiting implementation.
    
    Default: 100 requests per minute per IP.
    Flash sale endpoints: 10 requests per minute per user.
    """
    
    def __init__(
        self,
        cache: Optional["Cache"] = None,
        default_limit: int = 100,
        default_window: int = 60,
    ):
        """
        Initialize rate limiter.
        
        Args:
            cache: Redis cache instance
            default_limit: Requests allowed per window
            default_window: Window size in seconds
        """
        self._cache = cache
        self.default_limit = default_limit
        self.default_window = default_window
    
    async def check(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
    ) -> dict:
        """
        Check if request is allowed.
        
        Args:
            key: Unique identifier (IP, user_id, etc.)
            limit: Override default limit
            window: Override default window
            
        Returns:
            {
                "allowed": True/False,
                "remaining": int,
                "reset_at": datetime,
            }
            
        Raises:
            RateLimitExceeded: If limit exceeded
        """
        limit = limit or self.default_limit
        window = window or self.default_window
        
        # TODO: Implement with Redis
        # cache_key = f"ratelimit:{key}"
        # current = await self._cache._client.incr(cache_key)
        # 
        # if current == 1:
        #     # First request, set expiry
        #     await self._cache._client.expire(cache_key, window)
        # 
        # ttl = await self._cache._client.ttl(cache_key)
        # reset_at = datetime.utcnow() + timedelta(seconds=ttl)
        # 
        # if current > limit:
        #     raise RateLimitExceeded(
        #         retry_after=ttl,
        #         detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
        #     )
        # 
        # return {
        #     "allowed": True,
        #     "remaining": limit - current,
        #     "reset_at": reset_at,
        # }
        
        raise NotImplementedError("RateLimiter.check not implemented")
    
    def limit(
        self,
        requests: int = 100,
        window: int = 60,
        key_func: Optional[Callable[[Request], str]] = None,
    ):
        """
        Decorator/dependency for rate limiting endpoints.
        
        Args:
            requests: Max requests per window
            window: Window size in seconds
            key_func: Function to extract rate limit key from request
            
        Usage:
            @router.post("/orders")
            async def create_order(
                _: None = Depends(rate_limiter.limit(10, 60)),
            ):
                ...
        """
        # TODO: Implement
        # async def dependency(request: Request):
        #     if key_func:
        #         key = key_func(request)
        #     else:
        #         key = request.client.host
        #     
        #     await self.check(key, requests, window)
        # 
        # return dependency
        raise NotImplementedError("RateLimiter.limit not implemented")


# =============================================================================
# MIDDLEWARE
# =============================================================================

class RateLimitMiddleware:
    """
    Global rate limiting middleware.
    
    Applies default limits to all requests.
    Specific endpoints can have stricter limits via dependency.
    """
    
    def __init__(
        self,
        app,
        cache: Optional["Cache"] = None,
        default_limit: int = 100,
        default_window: int = 60,
    ):
        self.app = app
        self.limiter = RateLimiter(cache, default_limit, default_window)
    
    async def __call__(self, scope, receive, send):
        """
        ASGI middleware entry point.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # TODO: Implement middleware
        # request = Request(scope)
        # client_ip = request.client.host
        # 
        # try:
        #     await self.limiter.check(client_ip)
        # except RateLimitExceeded as e:
        #     # Return 429 response
        #     response = JSONResponse(
        #         status_code=429,
        #         content={"detail": e.detail},
        #         headers={"Retry-After": str(e.headers["Retry-After"])},
        #     )
        #     await response(scope, receive, send)
        #     return
        # 
        # await self.app(scope, receive, send)
        
        await self.app(scope, receive, send)


# =============================================================================
# FLASH SALE SPECIFIC
# =============================================================================

class FlashSaleRateLimiter:
    """
    Specialized rate limiter for flash sale endpoints.
    
    Features:
    - Per-user limits (not IP)
    - Stricter limits during sale window
    - Fair queuing (TODO)
    """
    
    def __init__(self, cache: Optional["Cache"] = None):
        self._cache = cache
        # During flash sale: 10 requests per minute per user
        self.sale_limit = 10
        self.sale_window = 60
    
    async def check_order_rate(self, user_id: str) -> dict:
        """
        Check if user can place order.
        
        Stricter limit than general API.
        
        Args:
            user_id: User's ID
            
        Returns:
            {"allowed": True, "remaining": int}
            
        Raises:
            RateLimitExceeded: If limit exceeded
        """
        # TODO: Implement
        # key = f"order_rate:{user_id}"
        # ...
        raise NotImplementedError("check_order_rate not implemented")


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# TODO: Initialize when cache is ready
# rate_limiter = RateLimiter()
# flash_sale_limiter = FlashSaleRateLimiter()

async def get_rate_limiter() -> RateLimiter:
    """FastAPI dependency for rate limiter."""
    # TODO: Return global instance
    raise NotImplementedError("get_rate_limiter not implemented")
```

---

# Schemas

## Order Schemas (Extended)

**File**: `app/schemas/order_schema.py` (additions to existing)

```python
"""
Order Schemas - Flash Sale Engine
==================================

Extended Pydantic models for order operations.
Add these to the existing order_schema.py file.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class OrderCreate(BaseModel):
    """Request body for creating an order."""
    
    product_id: UUID = Field(..., description="Product to purchase")
    quantity: int = Field(
        ...,
        ge=1,
        le=10,
        description="Quantity (1-10 per order)",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "quantity": 1,
            }
        }


class OrderCancel(BaseModel):
    """Request body for cancelling an order."""
    
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Cancellation reason",
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class OrderResponse(BaseModel):
    """Response for single order."""
    
    id: UUID
    user_id: UUID
    product_id: UUID
    quantity: int
    unit_price: float
    total_amount: float
    status: str
    payment_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OrderPlacedResponse(BaseModel):
    """Response after placing an order."""
    
    order_id: UUID
    status: str = "pending"
    payment_url: str
    expires_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "payment_url": "https://checkout.razorpay.com/v1/checkout.js",
                "expires_at": "2024-01-15T10:15:00Z",
            }
        }


class OrderListResponse(BaseModel):
    """Response for paginated order list."""
    
    orders: List[OrderResponse]
    total: int
    limit: int
    offset: int


class OrderCancelledResponse(BaseModel):
    """Response after cancelling an order."""
    
    order_id: UUID
    status: str = "cancelled"
    refund_initiated: bool
    refund_amount: Optional[float] = None
```

---

## Auth Schemas

**File**: `app/schemas/auth_schema.py` (new file)

```python
"""
Auth Schemas - Flash Sale Engine
=================================

Pydantic models for authentication operations.
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class UserRegister(BaseModel):
    """Request body for user registration."""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars)",
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name",
    )
    phone: Optional[str] = Field(
        None,
        pattern=r"^\+?[1-9]\d{9,14}$",
        description="Phone number (E.164 format)",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe",
                "phone": "+919876543210",
            }
        }


class UserLogin(BaseModel):
    """Request body for user login."""
    
    email: EmailStr = Field(..., description="User's email")
    password: str = Field(..., description="User's password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""
    
    refresh_token: str = Field(..., description="Valid refresh token")


class PasswordChange(BaseModel):
    """Request body for password change."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class TokenResponse(BaseModel):
    """Response containing access token."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=3600, description="Token validity in seconds")
    refresh_token: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
            }
        }


class UserResponse(BaseModel):
    """Response containing user info."""
    
    id: UUID
    email: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Response for successful login."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
```

---

# Quick Reference

## File Locations

| Template | Target Path |
|----------|-------------|
| OrderService | `app/services/order_service.py` |
| StockService | `app/services/stock_service.py` |
| PaymentService | `app/services/payment_service.py` |
| UserService | `app/services/user_service.py` |
| Orders Router | `app/routers/orders.py` |
| Auth Router | `app/routers/auth.py` |
| Webhooks Router | `app/routers/webhooks.py` |
| Dependencies | `app/core/dependencies.py` |
| Cache | `app/core/cache.py` |
| Rate Limiter | `app/core/rate_limiter.py` |
| Order Schemas | `app/schemas/order_schema.py` |
| Auth Schemas | `app/schemas/auth_schema.py` |

## Implementation Order

1. **Phase 1 - MVP**
   - Auth Schemas → Auth Router
   - UserService
   - Dependencies (get_db, get_current_user)
   - Order Schemas → Orders Router
   - StockService → OrderService

2. **Phase 2 - Scale**
   - Cache
   - Rate Limiter
   - PaymentService → Webhooks Router

---

> **Note**: All templates use `NotImplementedError` placeholders. Replace with actual implementation when ready.
