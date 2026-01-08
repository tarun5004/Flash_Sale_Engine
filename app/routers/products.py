from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession   #DB session ka type (async)
from app.db.session import get_db   #har request pe ek naya DB session provide karega
from app.services.product_service import ProductService  #service layer jo business logic handle karega and always remember router kabhi business logic nahi likhta


from app.schemas.product_schema import (
    ProductCreateSchema,
    ProductResponseSchema,
)

router = APIRouter(
    prefix="/products",
    tags=["products"],
)

#First endpoint: Create a new product
@router.post(
    "",
    response_model=ProductResponseSchema,  #response schema mean jo data client ko bhejna hai
    status_code=status.HTTP_201_CREATED,    #201 mean resource successfully created
)

async def create_product(
    payload: ProductCreateSchema,
    session: AsyncSession = Depends(get_db),  #DB session dependency injection
):
    """
    Create a new product.

    Flow:
    Request → Router → Service → Repository → DB
    """
    
    service = ProductService(session)  #service layer ka instance create karo mean ek session sabhi methods me use hoga
    
    try:
        product = await service.create_product(
            name=payload.name,
            price=payload.price,
            stock=payload.stock,
        )
        return product
    
    except Exception as e:
        #