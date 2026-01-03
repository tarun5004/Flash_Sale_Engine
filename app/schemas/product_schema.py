from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class ProductRead(BaseModel):
    id: int
    name: str
    price: Decimal
    stock:int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True