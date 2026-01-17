from decimal import Decimal
from re import search
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.product_repo import ProductRepository

from typing import List, Optional


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
    
    """async def get_products(
        self,
        search: Optional[str] = None,
    ) -> List[Product]:
        
        if not search:
            return await self.product_repo.get_all_active()
        
        # 1) Clean search text
        search = search.strip().lower() #extra spaces hatao , case issue avoid karo
        
        # 2) split into words
        keywords = search.split()   #keywords = ["notebook", "pro"]
        
        # 3) Call repo 
        return await self.product_repo.search_active_products_multi(keywords)  #service ne decide kiya , repo ne query ki 
# Later hum add kar sakte hain:
# AND logic (all words must match)
# Ranking (best match first)
# PostgreSQL Full Text Search
# ElasticSearch """




    async def get_products(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None, #hum optional search isslie use karte hain taaki user search na bhi kare to bhi chale
    ) -> List[Product]: #ye method paginated products return karega meaning limited number of products per page
        
        
        
        #Saftey rules
        if page < 1:
            raise ValueError("Page must be >= 1")
        
        if limit < 1 or limit > 50:
            raise ValueError("Limit must be between 1 and 50")
        
        offset = (page - 1) * limit
        
        keywords = None
        if search:
            search = search.strip().lower() #extra spaces hatao , case issue avoid karo
            keywords = search.split()  #keywords = ["notebook", "pro"] taaki hum bole ki inme se koi bhi word match kare
            
        return await self.product_repo.get_active_products_paginated(
            offset=offset,
            limit=limit,
            keywords=keywords,
        )

    # self- current ProductService object, >product_repo - us object ke andar jo repository ka object hai, .get_active_products_paginated() → repo ka ek function call
    # service ke pass repo ka phone number hai, service repo ko call kar raha hai 
    

    # =====================================================
    #Update stock method
    # =====================================================
    
    async def update_stock(
        self,
        product_id: int,
        new_stock: int,
    ) -> Product:
        try:
            # 1) Validation business rules
            if new_stock < 0:
                raise ValueError("Stock cannot be negative")
                
            # 2) Product fetch with lock
            product = await self.product_repo.get_by_id_for_update(product_id)
            if product is None:
                raise ValueError(f"Product with id {product_id} does not found")
            product.stock = new_stock  #3) Update ORM object
            await self.session.commit()  #4) Commit transaction
            return product
        except Exception:
            await self.session.rollback() #5) Rollback in case of error
            raise   


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
        
        
        
        
