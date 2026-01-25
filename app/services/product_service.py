from decimal import Decimal
from re import search
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.product_repo import ProductRepository

from typing import List, Optional

from app.models.product_image import ProductImage

from app.schemas.product_schema import ProductResponseSchema


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
    ) -> ProductResponseSchema:
        try:
            self._validate_name(name)
            self._validate_price(price)
            self._validate_stock(stock)

            product = Product(
                name=name,
                price=price,
                stock=stock,
                is_active=True,
            )

            await self.product_repo.create(product)
            await self.session.commit()
            
            # ✅ FIX: Refresh BEFORE accessing attributes
            # WHY: commit() expires ORM object, refresh() reloads it
            await self.session.refresh(product)

            return self._to_response(product)

        except Exception:
            await self.session.rollback()
            raise

    # PUBLIC SERVICE METHOD → UPDATE PRICE
    async def update_price(
        self,
        product_id: int,
        new_price: Decimal,
    ) -> ProductResponseSchema:
        try:
            self._validate_price(new_price)
            self._validate_product_id(product_id)

            product = await self._get_product_or_fail(product_id)

            if product.price == new_price:
                raise ValueError(
                    "New price must be different from the current price"
                )

            product.price = new_price
            await self.session.commit()
            
            # ✅ FIX: Refresh after commit
            await self.session.refresh(product)

            return self._to_response(product)

        except Exception:
            await self.session.rollback()
            raise

    # PUBLIC SERVICE METHOD - APPLY DISCOUNT
    async def apply_discount(
        self,
        product_id: int,
        discount_percent: Decimal,
    ) -> ProductResponseSchema:
        try:
            self._validate_product_id(product_id)
            self._validate_discount_percentage(discount_percent)
            
            product = await self._get_product_or_fail(product_id)
            
            discounted_price = product.price - (
                product.price * discount_percent / Decimal(100)
            )
            
            if discounted_price <= 0:
                raise ValueError("Discounted price must be greater than zero")
            
            product.price = discounted_price
            await self.session.commit()
            
            # ✅ FIX: Refresh after commit
            await self.session.refresh(product)
            
            return self._to_response(product)
        except Exception:
            await self.session.rollback()
            raise

    # GET PRODUCTS WITH PAGINATION
    async def get_products(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
    ) -> List[ProductResponseSchema]:
        
        self._validate_pagination(page, limit)
        
        if search:
            self._validate_search_query(search)
        
        offset = (page - 1) * limit
        
        keywords = None
        if search:
            search = search.strip().lower()
            keywords = search.split()
            
        products = await self.product_repo.get_active_products_paginated(
            offset=offset,
            limit=limit,
            keywords=keywords,
        )
        
        # ✅ FIX: No refresh needed here (no commit happened)
        # Products are already loaded from DB
        return [self._to_response(p) for p in products]

    # Update stock method
    async def update_stock(
        self,
        product_id: int,
        new_stock: int,
    ) -> ProductResponseSchema:
        try:
            self._validate_product_id(product_id)
            self._validate_stock(new_stock)
                
            product = await self.product_repo.get_by_id_for_update(product_id)
            if product is None:
                raise ValueError(f"Product with id {product_id} not found")
            
            product.stock = new_stock
            await self.session.commit()
            
            # ✅ FIX: Refresh after commit
            await self.session.refresh(product)
            
            return self._to_response(product)
        except Exception:
            await self.session.rollback()
            raise   

    # Update name method
    async def update_name(
        self,
        product_id: int,
        new_name: str,
    ) -> ProductResponseSchema:
        try:
            self._validate_product_id(product_id)
            self._validate_name(new_name)
            
            product = await self.product_repo.get_by_id_for_update(product_id)
            if product is None:
                raise ValueError(f"Product with id {product_id} not found")
            
            cleaned_name = new_name.strip()
            if product.name == cleaned_name:
                raise ValueError("New name must be different from the current name")
            
            product.name = cleaned_name
            await self.session.commit()
            
            # ✅ FIX: Refresh after commit
            await self.session.refresh(product)
            
            return self._to_response(product)
        except Exception:
            await self.session.rollback()
            raise

    # Activate product method
    async def activate_product(
        self, 
        product_id: int
    ) -> ProductResponseSchema:
        try:
            self._validate_product_id(product_id)
            
            product = await self.product_repo.get_by_id_for_update(product_id)
            if product is None:
                raise ValueError(f"Product with id {product_id} not found")
            
            if product.is_active:
                raise ValueError("Product is already active")
            
            product.is_active = True
            await self.session.commit()
            
            # ✅ FIX: Refresh after commit
            await self.session.refresh(product)
            
            return self._to_response(product)
        except Exception:   
            await self.session.rollback()
            raise
        
    # Deactivate product method
    async def deactivate_product(
        self, 
        product_id: int
    ) -> ProductResponseSchema:
        try:
            self._validate_product_id(product_id)
            
            product = await self.product_repo.get_by_id_for_update(product_id)
            if product is None:
                raise ValueError(f"Product with id {product_id} not found")
            
            product.is_active = False
            await self.session.commit()
            
            # ✅ FIX: Refresh after commit
            await self.session.refresh(product)
            
            return self._to_response(product)
        except Exception:
            await self.session.rollback()
            raise   

    # Add product image method
    async def add_product_image(
        self,
        product_id: int,
        image_url: str,
    ):
        try:
            self._validate_product_id(product_id)
            self._validate_image_url(image_url)
            
            product = await self.product_repo.get_by_id_for_update(product_id)
            if product is None:
                raise ValueError(f"Product with id {product_id} not found")
            
            image = ProductImage(
                product_id=product.id,
                image_url=image_url.strip(),
            )
            self.session.add(image)
            await self.session.commit()
            
            # ✅ FIX: Refresh after commit
            await self.session.refresh(image)
            
            return image
        except Exception:
            await self.session.rollback()
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
    
    
    def _to_response(self, product) -> ProductResponseSchema:
        """
        ✅ ORM Object → Pydantic Schema converter
        
        WHY THIS IS CRITICAL:
        =====================
        1. ORM object has DB connection → Lazy loading possible
        2. Pydantic Schema is PLAIN DATA → No DB connection
        3. Plain data can be serialized safely outside async context
        4. Prevents MissingGreenlet error
        
        WHEN TO USE:
        ============
        - Always call this before returning from any service method
        - Never return raw ORM object to router
        """
        return ProductResponseSchema(
            id=product.id,
            name=product.name,
            price=float(product.price),
            stock=product.stock,
            is_active=product.is_active,
            created_at=product.created_at,
            # ✅ FIX: Handle NULL updated_at (new products have NULL)
            updated_at=product.updated_at if product.updated_at else product.created_at,
        )
    

    # =====================================================
    # VALIDATION HELPERS (STATIC METHODS)
    # =====================================================
    # 📌 ORIGINAL VALIDATORS (Already existed)
    # =====================================================
    
    @staticmethod
    def _validate_name(name: str):
        """Validate product name (3-255 characters)"""
        if not name or len(name) < 3:
            raise ValueError("Name must be at least 3 characters long")
        # ✅ NEW: Max length check added
        if len(name) > 255:
            raise ValueError("Name must be less than 255 characters")

    @staticmethod
    def _validate_price(price: Decimal):
        """Validate product price (must be positive, max limit)"""
        if price <= 0:
            raise ValueError("Price must be greater than zero")
        # ✅ NEW: Max price limit added (prevent overflow)
        if price > Decimal("9999999.99"):
            raise ValueError("Price cannot exceed 9,999,999.99")

    @staticmethod
    def _validate_stock(stock: int):
        """Validate stock quantity (non-negative, max limit)"""
        if stock < 0:
            raise ValueError("Stock cannot be negative")
        # ✅ NEW: Max stock limit added (prevent abuse)
        if stock > 1000000:
            raise ValueError("Stock cannot exceed 1,000,000")

    @staticmethod
    def _validate_product_id(product_id: int):
        """Validate product ID (must be positive integer)"""
        if product_id <= 0:
            raise ValueError("Product ID must be positive")
        
    @staticmethod
    def _validate_discount_percentage(discount_percent: Decimal):
        """Validate discount (must be between 0 and 100 exclusive)"""
        if discount_percent <= 0:
            raise ValueError("Discount percentage must be greater than zero")
        if discount_percent >= 100:
            raise ValueError("Discount percentage must be less than 100")


    # =====================================================
    # 🆕 NEW VALIDATORS (Added for security & validation)
    # =====================================================
    # 📌 Added on: January 2026
    # 📌 Purpose: Enhanced input validation for production use
    # =====================================================

    @staticmethod
    def _validate_image_url(image_url):
        """
        🆕 NEW VALIDATOR - Added for add_product_image()
        
        Purpose: Validate image URL format and security
        
        Checks:
        1. Not empty
        2. Max length 2048 (standard URL limit)
        3. Must start with http:// or https://
        4. Must end with valid image extension
        
        Note: image_url can be str OR HttpUrl (Pydantic type)
        """
        # ✅ FIX: Convert HttpUrl to string first
        url_str = str(image_url) if image_url else ""
        
        if not url_str or len(url_str.strip()) == 0:
            raise ValueError("Image URL cannot be empty")
        
        if len(url_str) > 2048:
            raise ValueError("Image URL is too long (max 2048 characters)")
        
        # Basic URL format check
        clean_url = url_str.strip().lower()
        if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
            raise ValueError("Image URL must start with http:// or https://")
        
        # Check for valid image extension
        valid_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")
        has_valid_ext = any(clean_url.endswith(ext) for ext in valid_extensions)
        if not has_valid_ext:
            raise ValueError(f"Image URL must end with one of: {valid_extensions}")

    @staticmethod
    def _validate_search_query(search: str):
        """
        🆕 NEW VALIDATOR - Added for get_products()
        
        Purpose: Validate search query for security
        
        Checks:
        1. Max length 100 characters
        2. No SQL injection characters
        """
        if search and len(search) > 100:
            raise ValueError("Search query too long (max 100 characters)")
        
        # Block dangerous SQL characters (basic protection)
        dangerous_patterns = [";", "--", "/*", "*/", "DROP", "DELETE", "UPDATE", "INSERT"]
        search_upper = search.upper() if search else ""
        for pattern in dangerous_patterns:
            if pattern in search_upper:
                raise ValueError("Invalid characters in search query")


    @staticmethod
    def _validate_pagination(page: int, limit: int):
        """
        🆕 NEW VALIDATOR - Added for get_products()
        
        Purpose: Validate pagination parameters
        
        Checks:
        1. Page must be >= 1 and <= 10000
        2. Limit must be >= 1 and <= 100
        
        Why: Prevents DoS attacks via excessive data requests
        """
        if page < 1:
            raise ValueError("Page must be >= 1")
        if page > 10000:
            raise ValueError("Page number too high (max 10,000)")
        if limit < 1:
            raise ValueError("Limit must be >= 1")
        if limit > 100:
            raise ValueError("Limit too high (max 100 per page)")


    @staticmethod
    def _validate_quantity(quantity: int):
        """
        🆕 NEW VALIDATOR - For future Order Service
        
        Purpose: Validate order quantity
        
        Checks:
        1. Must be positive
        2. Max 100 items per order
        
        Why: Prevents inventory abuse and bulk order attacks
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        if quantity > 100:
            raise ValueError("Cannot order more than 100 items at once")




