"""Order Model - Flash Sale Engine

🐛 BUGS FIXED:
1. Enum() mein extra parenthesis tha: Enum((OrderStatus)...) -> Enum(OrderStatus)
2. OrderStatus class Order se pehle define hona zaroori tha
"""
from sqlalchemy import Column, Integer, ForeignKey, Enum, Numeric, DateTime, func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class OrderStatus(enum.Enum):
    """Order ke possible states"""
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User")
    product = relationship("Product")