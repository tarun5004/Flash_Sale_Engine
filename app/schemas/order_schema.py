from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from enum import Enum

class OrderStatusSchema(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    
    
class OrderCreate(BaseModel):
    product_id: int
    quantity: int
    
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than zero")
        return v

    
class OrderRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    total_amount: Decimal
    status: OrderStatusSchema
    created_at: datetime

    class Config:
        from_attributes = True
