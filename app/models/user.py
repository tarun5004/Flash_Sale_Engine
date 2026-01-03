from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Integer, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())