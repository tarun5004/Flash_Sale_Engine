"""
Payment Service — simulated payment gateway for development.
Layer: Service (called by OrderService after order creation)

Deterministic rules:
    - Every 5th order (id % 5 == 0) → FAILED — exercises the compensation path
    - All other orders → SUCCESS
Replace this class with a real payment gateway adapter in production.
"""

from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus


class PaymentService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def charge(
        self,
        order_id: int,
        amount: Decimal,
    ) -> Payment:
        """
        Process payment for an order.
        Returns a Payment record regardless of outcome — both success and failure are persisted.
        """
        succeeded = self._should_succeed(order_id)

        payment_status = PaymentStatus.SUCCESS if succeeded else PaymentStatus.FAILED
        # Transaction ref is only meaningful on success
        transaction_ref = f"FAKE-TXN-{order_id}-{uuid4().hex[:8]}" if succeeded else None

        payment = Payment(
            order_id=order_id,
            provider="fake-gateway",
            status=payment_status,
            transaction_ref=transaction_ref,
        )

        self.session.add(payment)
        # Flush to persist payment record — commit is handled by the caller (OrderService)
        await self.session.flush()

        return payment

    @staticmethod
    def _should_succeed(order_id: int) -> bool:
        """
        Deterministic success/failure based on order ID.
        Every 5th order fails — gives a predictable way to test the failure/compensation path.
        """
        return order_id % 5 != 0
