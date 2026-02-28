"""Cart Repository — DB queries for cart_items table."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload

from app.models.cart_item import CartItem


class CartRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_and_product(
        self, user_id: int, product_id: int
    ) -> CartItem | None:
        """Check if a specific product is already in the user's cart."""
        result = await self.session.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_user_cart(self, user_id: int) -> list[CartItem]:
        """Fetch all cart items for a user, with product eagerly loaded."""
        result = await self.session.execute(
            select(CartItem)
            .options(joinedload(CartItem.product))
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.added_at.desc())
        )
        return list(result.scalars().unique().all())

    async def add(self, cart_item: CartItem) -> CartItem:
        self.session.add(cart_item)
        await self.session.flush()
        return cart_item

    async def delete_item(self, cart_item: CartItem) -> None:
        await self.session.delete(cart_item)
        await self.session.flush()

    async def clear_user_cart(self, user_id: int) -> int:
        """Remove all items from a user's cart. Returns count deleted."""
        result = await self.session.execute(
            delete(CartItem).where(CartItem.user_id == user_id)
        )
        await self.session.flush()
        return result.rowcount
