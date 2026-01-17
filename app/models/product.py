from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, func
from app.db.base import Base
from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
    )