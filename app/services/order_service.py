from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.repositories.product_repo import ProductRepository
from app.repositories.order_repo import OrderRepository

class OrderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.order_repo = OrderRepository(session)
        self.product_repo = ProductRepository(session)



    async def create_order(
            self,
            user_id: int,
            product_id: int,
            quantity: int
        ) -> Order:

        """
        Create a new order after validating product availability and stock.
        - Stock locking is handled at the database level to prevent overselling.
        - no over-selling.
        - Ensures that the product exists and has sufficient stock.
        - atomic trasnaction
        """

        try:
            product = await self.product_repo.get_by_id_for_update(product_id)

            if not product:
                raise ValueError("Product does not exist.")
            
            if not product.is_active:
                raise ValueError("Product is not active.")
            
            # check stock after lock
            if product.stock < quantity:
                raise ValueError("Insufficient stock for the product.")
            

            # Deduct stock
            product.stock -= quantity

            # Calculate total
            total_amount = Decimal(product.price) * quantity

            # Create order
            order = Order(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                total_amount=total_amount,
                status=OrderStatus.PENDING  # Initial status
            )

            await self.order_repo.create(order)

            # commit once (stock + order)
            await self.session.commit()

            return order
        
        except Exception as e:
            await self.session.rollback()
            raise e
