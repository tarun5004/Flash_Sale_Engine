from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.product_repo import ProductRepository

from typing import List, Optional
from app.models.product import Product

"""
Industry Rule (IMPORTANT):
Service code should read like English.

Service layer ka kaam:
- Business rules apply karna
- Validation karna
- Transaction handle karna
- Repository ko coordinate karna

Service DIRECT SQL nahi likhti.
"""

class ProductService:
    def __init__(self, session: AsyncSession):
        # Dependency Injection:
        # Session bahar se milta hai, hum khud nahi banate
        self.session = session

        # Repository bhi inject hoti hai
        self.product_repo = ProductRepository(session)

    # =====================================================
    # PUBLIC SERVICE METHOD → CREATE PRODUCT
    # =====================================================
    async def create_product(
        self,
        name: str,
        price: Decimal,
        stock: int,
    ) -> Product:
        try:
            # 1) Validation = business logic
            # Never trust input. Always validate.
            # Validation ka matlab:
            # "Database ko corrupt hone se bachana"
            self._validate_name(name)
            self._validate_price(price)
            self._validate_stock(stock)

            # 2) Create ORM object
            """
            We create ORM objects because we want to treat a database
            row like a Python object — so that we can work with Python
            instead of writing raw SQL queries.
            """
            product = Product(
                name=name,
                price=price,
                stock=stock,
                is_active=True,
            )

            # 3) Save to DB via repository
            # Repository ka kaam sirf DB access hota hai
            await self.product_repo.create(product)

            # 4) Commit transaction
            await self.session.commit()

            return product

        except Exception:
            # 5) Rollback in case of any error
            # Industry rule: transaction must be safe
            await self.session.rollback()
            raise

    # PUBLIC SERVICE METHOD → UPDATE PRICE
    async def update_price(
        self,
        product_id: int,
        new_price: Decimal,
    ) -> Product:
        try:
            # 1) Validate input
            self._validate_price(new_price)
            self._validate_product_id(product_id)

            # 2) Fetch product with FOR UPDATE lock
            """
            _get_product_or_fail() isliye banaya gaya hai taaki:
            - with_for_update() (row lock)
            - error handling
            dono ek clean, reusable helper me aa jaayein
            """
            product = await self._get_product_or_fail(product_id)

            # 3) Business rule check
            if product.price == new_price:
                raise ValueError(
                    "New price must be different from the current price"
                )

            # 4) Update ORM object
            # ORM automatically change track karta hai
            product.price = new_price

            # 5) Commit transaction
            await self.session.commit()

            return product

        except Exception:
            # 6) Rollback in case of error
            await self.session.rollback()
            raise

    # ✅ FIX: apply_discount method ko class level pe laana tha (4 spaces indent)
    # ❌ GALTI: Ye method update_price ke ANDAR indent ho gaya tha (8 spaces)
    # 📌 RULE: Python mein indentation = scope. Galat indent = nested function ban jaata hai
    #
    # ✅ FIX 2: Parameter naam "discount_percent" hona chahiye (test file mein yahi use ho raha hai)
    # ❌ GALTI: "discount_percentage" likha tha lekin test mein "discount_percent" call ho raha tha
    # 📌 RULE: Function signature aur caller mein parameter names match hone chahiye
    
    #====================================================
    # PUBLIC SERVICE METHOD - APPLY DISCOUNT
    #====================================================
    
    async def apply_discount(
        self,
        product_id: int,
        discount_percent: Decimal,  # ✅ Fixed: discount_percentage -> discount_percent
    ) -> Product:
        try:
            # 1) Validate input
            self._validate_product_id(product_id)
            self._validate_discount_percentage(discount_percent)  # ✅ Use proper validator
            
            # 2) Fetch product with FOR UPDATE lock
            product = await self._get_product_or_fail(product_id)
            
            # 3) Calculate discounted price
            discounted_price = product.price - (
                product.price * discount_percent / Decimal(100)
            )
            
            # 4) Final safety check
            if discounted_price <= 0:
                raise ValueError("Discounted price must be greater than zero")
            
            # 5) Update ORM object
            product.price = discounted_price
            
            # 6) Commit transaction
            await self.session.commit()
            
            return product
        except Exception:
            # 7) Rollback in case of error
            await self.session.rollback()
            raise
        
        
        
    # =====================================================
    #GET PRODUCT BY ID (OPTIONAL)
    # =====================================================
    
    async def get_products(
        self,
        search: Optional[str] = None,
    ) -> list[Product]:
        
        products = await self.product_repo.get_all_active()
        
        #simple search filter and business logic
        if search:
            products = [
                p for p in products
                if search.lower() in p.name.lower()
            ]
        return products    
    
    
    
# =====================================================    
# PRIVATE HELPER METHODS (OOP CONCEPT)
# =====================================================
    async def _get_product_or_fail(self, product_id: int) -> Product:
        """
        Helper method ka role:
        - Product fetch karna
        - DB row ko lock karna (FOR UPDATE)
        - Agar product na mile to error throw karna
        """
        product = await self.product_repo.get_by_id_for_update(product_id)

        if product is None:
            raise ValueError(f"Product with id {product_id} does not exist")

        return product

    # VALIDATION HELPERS (STATIC METHODS)
    @staticmethod
    def _validate_name(name: str):
        if not name or len(name) < 3:
            raise ValueError("Name must be at least 3 characters long")

    @staticmethod
    def _validate_price(price: Decimal):
        if price <= 0:
            raise ValueError("Price must be greater than zero")

    @staticmethod
    def _validate_stock(stock: int):
        if stock < 0:
            raise ValueError("Stock cannot be negative")

    @staticmethod
    def _validate_product_id(product_id: int):
        if product_id <= 0:
            raise ValueError("Product ID must be positive")
        
    @staticmethod
    def _validate_discount_percentage(discount_percent: Decimal):
        if discount_percent <= 0:
            raise ValueError("Discount percentage must be greater than zero")
        
        if discount_percent >= 100:
            raise ValueError("Discount percentage must be less than 100")
            
