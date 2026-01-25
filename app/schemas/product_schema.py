from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class ProductCreateSchema(BaseModel):
    name: str
    price: Decimal
    stock: int
    
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Price must be non-negative")
        return v

class ProductResponseSchema(BaseModel): #response schema for product jisse koi extra fields na mile 
    id: int
    name: str
    price: Decimal
    stock:int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        
class ProductUpdatepriceSchema(BaseModel):
    price: Decimal
    
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Price must be non-negative")
        return v

class ProductApplyDiscountSchema(BaseModel):
    discount_percentage: Decimal