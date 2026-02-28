"""Cart Schemas — request/response contracts for cart operations."""
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class CartItemAdd(BaseModel):
    """Add item to cart."""
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    """Update cart item quantity."""
    quantity: int


class CartItemRead(BaseModel):
    """Single cart item response."""
    id: int
    product_id: int
    product_name: str
    product_price: Decimal
    product_stock: int
    quantity: int
    subtotal: Decimal
    added_at: datetime

    class Config:
        from_attributes = True


class CartSummary(BaseModel):
    """Full cart with total."""
    items: list[CartItemRead]
    total: Decimal
    item_count: int
