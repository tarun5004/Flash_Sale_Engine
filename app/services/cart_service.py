"""
Cart Service — manages user shopping cart logic.
Layer: Service (between Router and Repository)
Responsibilities: add/update/remove cart items, validate stock, build cart summary.
"""

from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart_item import CartItem
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.cart_schema import CartItemRead, CartSummary


class CartService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.cart_repo = CartRepository(session)
        self.product_repo = ProductRepository(session)

    async def add_item(self, user_id: int, product_id: int, quantity: int) -> CartItemRead:
        """
        Add a product to the cart, or increase quantity if already present.
        Validates product exists & is active. Does NOT deduct stock (that's at order time).
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            raise ValueError("Product not found.")
        if not product.is_active:
            raise ValueError("Product is not available.")

        # Check if already in cart — increment instead of duplicate
        existing = await self.cart_repo.get_by_user_and_product(user_id, product_id)

        if existing:
            existing.quantity += quantity
            await self.session.commit()
            await self.session.refresh(existing, ["product"])
            return self._to_item_read(existing)
        else:
            item = CartItem(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
            )
            created = await self.cart_repo.add(item)
            await self.session.commit()
            await self.session.refresh(created, ["product"])
            return self._to_item_read(created)

    async def get_cart(self, user_id: int) -> CartSummary:
        """Fetch the user's full cart with product details and totals."""
        items = await self.cart_repo.get_user_cart(user_id)
        item_reads = [self._to_item_read(it) for it in items]
        total = sum(it.subtotal for it in item_reads)
        return CartSummary(
            items=item_reads,
            total=total,
            item_count=len(item_reads),
        )

    async def update_item_quantity(
        self, user_id: int, item_id: int, quantity: int
    ) -> CartItemRead:
        """Update quantity of a specific cart item. Quantity=0 removes it."""
        items = await self.cart_repo.get_user_cart(user_id)
        target = next((it for it in items if it.id == item_id), None)

        if target is None:
            raise ValueError("Cart item not found.")

        if quantity <= 0:
            await self.cart_repo.delete_item(target)
            await self.session.commit()
            # Return the deleted item info
            return self._to_item_read(target)

        target.quantity = quantity
        await self.session.commit()
        await self.session.refresh(target, ["product"])
        return self._to_item_read(target)

    async def remove_item(self, user_id: int, item_id: int) -> None:
        """Remove a specific item from the cart."""
        items = await self.cart_repo.get_user_cart(user_id)
        target = next((it for it in items if it.id == item_id), None)

        if target is None:
            raise ValueError("Cart item not found.")

        await self.cart_repo.delete_item(target)
        await self.session.commit()

    async def clear_cart(self, user_id: int) -> int:
        """Remove everything from the cart. Returns number of items removed."""
        count = await self.cart_repo.clear_user_cart(user_id)
        await self.session.commit()
        return count

    @staticmethod
    def _to_item_read(item: CartItem) -> CartItemRead:
        """ORM → Pydantic conversion — prevents MissingGreenlet."""
        product = item.product
        subtotal = Decimal(str(product.price)) * item.quantity
        return CartItemRead(
            id=item.id,
            product_id=item.product_id,
            product_name=product.name,
            product_price=product.price,
            product_stock=product.stock,
            quantity=item.quantity,
            subtotal=subtotal,
            added_at=item.added_at,
        )
