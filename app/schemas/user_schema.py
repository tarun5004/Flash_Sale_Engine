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
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Separate from UserCreate — login may diverge (e.g. 2FA fields later)"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT response contract — matches OAuth2 password flow spec"""
    access_token: str
    token_type: str = "bearer"
        
        
        
"""
JWT LOGIC
IS user ka token bana do
30 minute ke liye
SECRET_KEY se sign karke


login work = verify identity
Authorization work = Give permission
"""