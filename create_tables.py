import asyncio
from app.db.session import engine
from app.db.base import Base

# 👇 IMPORTANT: yahan models import karo
from app.models.product import Product
from app.models.user import User
from app.models.order import Order
from app.models.payment import Payment

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(main())
