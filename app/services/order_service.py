"""
Order Service — orchestrates the full order lifecycle.
Layer: Service (coordinates Repository, PaymentService, and transaction boundaries)

Flow:
  1. Lock product row (SELECT FOR UPDATE) → prevents concurrent overselling
  2. Validate stock availability
  3. Deduct stock + create PENDING order (single flush, no commit yet)
  4. Call PaymentService
  5. On payment success → mark PAID, commit everything
  6. On payment failure → compensate stock, mark FAILED, commit (order record preserved)
  7. On unexpected error → full rollback, nothing persisted
"""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.payment import PaymentStatus
from app.repositories.product_repo import ProductRepository
from app.repositories.order_repo import OrderRepository
from app.services.payment_service import PaymentService
from app.schemas.order_schema import OrderRead


class OrderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.order_repo = OrderRepository(session)
        self.product_repo = ProductRepository(session)
        self.payment_service = PaymentService(session)

    async def create_order(
        self,
        user_id: int,
        product_id: int,
        quantity: int,
    ) -> OrderRead:
        """
        Full order creation with payment and compensation.
        Single transaction boundary — stock + order + payment all commit or rollback together.
        """
        try:
            # --- Step 1: Lock product row to prevent concurrent stock modification ---
            product = await self.product_repo.get_by_id_for_update(product_id)

            if not product:
                raise ValueError("Product does not exist.")

            if not product.is_active:
                raise ValueError("Product is not active.")

            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero.")

            # Stock check AFTER lock — ensures no race condition between read and deduct
            if product.stock < quantity:
                raise ValueError(
                    f"Insufficient stock. Available: {product.stock}, requested: {quantity}"
                )

            # --- Step 2: Deduct stock optimistically ---
            product.stock -= quantity

            # Snapshot price at order time — protects against price changes after ordering
            total_amount = Decimal(str(product.price)) * quantity

            # --- Step 3: Create order as PENDING ---
            order = Order(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                total_amount=total_amount,
                status=OrderStatus.PENDING,
            )
            created_order = await self.order_repo.create(order)

            # --- Step 4: Process payment ---
            payment = await self.payment_service.charge(
                order_id=created_order.id,
                amount=total_amount,
            )

            # --- Step 5: Update order status based on payment result ---
            if payment.status == PaymentStatus.SUCCESS:
                created_order.status = OrderStatus.PAID
            else:
                # Payment failed — compensate stock inline, keep order as FAILED for audit
                created_order.status = OrderStatus.FAILED
                product.stock += quantity

            # Single commit: stock change + order + payment all persisted atomically
            await self.session.commit()
            await self.session.refresh(created_order)

            return self._to_response(created_order)

        except Exception:
            await self.session.rollback()
            raise

    async def get_user_orders(self, user_id: int) -> list[OrderRead]:
        """Fetch all orders for the authenticated user."""
        orders = await self.order_repo.get_by_user_id(user_id)
        return [self._to_response(o) for o in orders]

    @staticmethod
    def _to_response(order: Order) -> OrderRead:
        """ORM → Pydantic conversion — prevents MissingGreenlet outside async context."""
        return OrderRead(
            id=order.id,
            user_id=order.user_id,
            product_id=order.product_id,
            quantity=order.quantity,
            total_amount=order.total_amount,
            status=order.status.value,
            created_at=order.created_at,
        )
