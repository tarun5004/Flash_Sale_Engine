import asyncio
from app.db.session import async_session
from sqlalchemy import select
from app.models.product import Product

async def main():
    async with async_session() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        
        for p in products:
            print(p.id, p.name, p.price, p.stock)

asyncio.run(main())
