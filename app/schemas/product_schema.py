from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class ProductCreateSchema(BaseModel):
    name: str
    price: Decimal
    stock: int

class ProductResponseSchema(BaseModel):
    id: int
    name: str
    price: Decimal
    stock:int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        
class ProductUpdatepriceSchema(BaseModel):
    price: Decimal
    
class ProductApplyDiscountSchema(BaseModel):
    discount_percentage: Decimal