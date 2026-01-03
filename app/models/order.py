from sqlalchemy import (Column,
    Integer,
    ForeignKey,
    Enum,
    Numeric,
    DateTime, func,  )
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Foreign key to link orders to users
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False) # Foreign key to link orders to products
    
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    status = Column(Enum((OrderStatus), default=OrderStatus.PENDING, nullable=False)) # Order status using Enum mean to define possible order states
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User")    # Establish relationship with User model mean to link orders to users
    product = relationship("Product") # Establish relationship with Product model mean to link orders to products