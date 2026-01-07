"""Payment Model - Flash Sale Engine"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class PaymentStatus(enum.Enum):
    """Payment ke possible states"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    provider = Column(String(100), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)
    transaction_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    order = relationship("Order")