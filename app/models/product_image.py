from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProductImage(Base):
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),   #ondelete="CASCADE" → product delete/inactive hua → images auto clean
        nullable=False,
    )
    image_url = Column(String(500), nullable=False)   #image URL store karega image_url → frontend se aane wali URL
    
    product = relationship("Product", back_populates="images")