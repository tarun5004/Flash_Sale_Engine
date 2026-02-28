"""Cart Item Model — stores items in a user's shopping cart."""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    __table_args__ = (
        # One cart entry per (user, product) pair — quantity increments instead of duplicates
        UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
    )

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )

    quantity = Column(Integer, nullable=False, default=1)

    added_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships — eager-load product for cart display
    user = relationship("User")
    product = relationship("Product", lazy="joined")
