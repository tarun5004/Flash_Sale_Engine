from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class PaymentStatus(enum.Enum): #
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    
    class Payment(Base):
        __tablename__ = "payments"
        
        id = Column(Integer, primary_key=True)
        order_id = Column(Integer, ForeignKey("orders.id"), nullable=False) # Foreign key to link payments to orders
        
        
        provider = Column(String(100), nullable=False) # Payment provider name
        status = Column(Enum(PaymentStatus), nullable=False) # Payment status using Enum to define possible payment states
        transaction_ref = Column(String(255), nullable=True) # Reference ID from the payment gateway
        
        created_at = Column(DateTime, server_default=func.now())
        
        order = relationship("Order") # Establish relationship with Order model to link payments to orders