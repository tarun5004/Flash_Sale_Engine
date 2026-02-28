from sqlalchemy import(
    Column,
    Integer,
    Numeric,
    ForeignKey,
    DateTime,
    Enum as sqlEnum,
    CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"

class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_quantity_positive"),
    )

    id = Column(Integer, primary_key=True)

    user_id =Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, nullable=False)

    status = Column(
        sqlEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Precomputed at order time — avoids price drift if product price changes later
    total_amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user = relationship("User")
    # Eager-loaded — avoids extra queries when building order responses
    product = relationship("Product", lazy="joined")