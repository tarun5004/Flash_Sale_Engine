from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.product import Product
#ORM queries hamesha Model Class pe hoti hain,
#kabhi module ya lowercase name pe nahi


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
    
    async def search_active_products(self, keyword: str):
        stmt = (
            select(Product)
            .where(
                product.is_active == True,
                Product.name.ilike(f"%{keyword}%")  #ilike = case-insensitive LIKE %keyword% = kahin bhi ho
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    
    async def search_active_products_multi(self, keywords: list[str]):
        """
        keywords = ["notenook", "pro"]
        """
        conditions = [] #ye list SQL conditions store karegi like , name ILIKE '%notenook%', name ILIKE '%pro%'
        
        for word in keywords:        #har word ke liye partial match
            conditions.append(Product.name.ilike(f"%{word}%"))        #%word% = kahin bhi ho
            
        stmt = (
            select(Product)
            .where(
                Product.is_active == True,
                or_(*conditions)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    
    async def get_active_products_paginated(
        self,
        *,           #mean iske baad ke saare parameters sirf keyword arguments se hi pass honge.
        offset: int,
        limit: int,
        keywords: list[str] | None = None, #optional parameter mean karte hain taaki hum same method se search + normal listing dono kar saken
    ):
        stmt = select(Product).where(Product.is_active == True)
        
        #Search condition
        
        if keywords:
            conditions = [
                Product.name.ilike(f"%{word}%")
                for word in keywords
            ]
            stmt = stmt.where(or_(*conditions))
            
        # Pagination
        stmt = stmt.offset(offset).limit(limit)
        
        result = await self.session.execute(stmt)  #mean self - current ProductService ka object , session - uska DB session
        return result.scalars().all()
    
#offset / limit → DB-level pagination (FAST)
#keywords optional → same method handles search + normal list
#Repo sirf query likhta hai, decision nahi


async def get_by_id_for_update(self, product_id: int) -> Product | None:
    """
    row-level lock ke saath product fetch karta hai
    (future: order / stock concurrency ke liye base)
    
    """
    
    result = await self.session.execute(
        select(Product)
        .where(Product.id == product_id)
        .with_for_update()  #raw lock - jab tak transaction complete nahi hota tab tak koi or update nahi kar skta 
    )
    return result.scalar_one_or_none