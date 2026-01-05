from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session 

    # -------------------------
    # CREATE PRODUCT
    # -------------------------
    async def create(self, product: Product) -> Product:
        """
        Adds ORM object to session.
        Actual DB write happens on commit (service layer).
        """
        self.session.add(product)

        # flush = DB se ID generate karwa lo (commit nahi)
        await self.session.flush()

        return product

    # -------------------------
    # GET PRODUCT WITH LOCK
    # -------------------------
    async def get_by_id_for_update(self, product_id: int) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    # -------------------------
    # GET ALL ACTIVE PRODUCTS
    # -------------------------
    async def get_all_active(self):
        result = await self.session.execute(
            select(Product).where(Product.is_active == True)
        )
        return result.scalars().all()
