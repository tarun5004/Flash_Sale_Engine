from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel): #ye login input ke liye bhi use hoskta hai 
    email: EmailStr
    password: str
    
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v
    
class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str                          #admin or user
    created_at: datetime
    class Config:
        from_attributes = True
        
        
        
"""
JWT LOGIC
IS user ka token bana do
30 minute ke liye
SECRET_KEY se sign karke


login work = verify identity
Authorization work = Give permission
"""