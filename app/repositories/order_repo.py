"""Order Repository - Flash Sale Engine

🐛 BUG FIXED:
1. selectinload galat import tha: from sqlalchemy -> from sqlalchemy.orm
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload  # ✅ FIXED: sqlalchemy.orm se import karna hai
from app.models.order import Order


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
            
    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        return order
    
    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.product))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
        