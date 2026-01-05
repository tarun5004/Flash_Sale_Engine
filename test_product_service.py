import asyncio
from decimal import Decimal

from app.db.session import async_session
from app.services.product_service import ProductService

async def test():
    async with async_session() as session:
        service = ProductService(session)

        # 1️⃣ Create product
        product = await service.create_product(
            name="Test Product",
            price=Decimal("100"),
            stock=10
        )
        print("Created product:", product.id, product.price)

        # 2️⃣ Apply discount
        product = await service.apply_discount(
            product_id=product.id,
            discount_percent=Decimal("20")
        )
        print("After discount:", product.price)

asyncio.run(test())
