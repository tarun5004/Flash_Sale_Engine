from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True