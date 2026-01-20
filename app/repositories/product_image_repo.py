from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product_image import ProductImage

class ProductImageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
        async def create(self, image: ProductImage) -> ProductImage:
            self.session.add(image)
            await self.session.flush() #DB se ID generate karwa lo (commit nahi) flush se
            return image
        
        
        
        
        
        
        
# flush() = DB ko bolna “bhai abhi ID generate kar do, commit baad me hoga”