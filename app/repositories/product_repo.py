from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session 
        

    async def get_by_id_for_update(self, product_id: int) -> Product| None:
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()
    
    
    async def get_all_active(self):
        result = await self.session.execute(
            select(Product).where(Product.is_active == True)
        )
        return result.scalars().all()
    