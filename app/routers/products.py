from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession   #DB session ka type (async)
from app.db import session
from app.db.session import get_db   #har request pe ek naya DB session provide karega
from app.services.product_service import ProductService  #service layer jo business logic handle karega and always remember router kabhi business logic nahi likhta
from sqlalchemy import select
from fastapi import Query
from pydantic import BaseModel
from app.schemas.product_image_schema import (ProductImageCreate, ProductImageResponse,)

# router means HTTP endpoints ka grouping by DOMAIN (yaha domain = products)

from app.schemas.product_schema import (
    ProductCreateSchema,
    ProductResponseSchema,
    ProductUpdatepriceSchema,
    ProductApplyDiscountSchema,
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
        #business validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
        
        
@router.patch(
    "/{product_id}/price",
    response_model=ProductResponseSchema,
)
async def update_product_price(
    product_id: int,
    payload: ProductUpdatepriceSchema,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(session)
    try:
        product = await service.update_price(
            product_id=product_id,
            new_price=payload.price,
        )
        return product

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.patch(
    "/{product_id}/discount",
    response_model=ProductResponseSchema,
)
async def apply_product_discount(
        product_id: int,
        payload: ProductApplyDiscountSchema,
        session: AsyncSession = Depends(get_db)
):
    service = ProductService(session)
    try:
        product = await service.apply_discount(
            product_id=product_id,
            discount_percent=payload.discount_percentage,
        )
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
"""Flow:
Swagger → Router → ProductService.update_price()
        → Row lock → ORM update → commit → response"""
        
@router.get(
    "",
    response_model=list[ProductResponseSchema],
) 
async def get_products(
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    service = ProductService(session)
    return await service.get_products(search=search)

# ===============================================
# Advanced: Pagination, Filtering, Stock Update, Name Update, Activate/Deactivate, Add Image, Soft Delete
# ===============================================
@router.get(
    "",
    response_model=list[ProductResponseSchema],
)
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(session)
    
    return await service.get_products(
        page=page,
        limit=limit,
        search=search,
    )
    
    
class UpdateStockRequest(BaseModel):
    stock: int
    
@router.patch(
    "/{product_id}/stock",
    response_model=ProductResponseSchema,
)
async def update_product_stock(
    product_id: int,
    payload: UpdateStockRequest,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(session)
    return await service.update_stock(
        product_id=product_id,
        new_stock=payload.stock,
    )
    
    
    
    
class UpdateNameRequest(BaseModel): #request body schema for updating name
    name: str
    
    
@router.patch(
    "/{product_id}/name",
    response_model=ProductResponseSchema,
)
async def update_product_name(
    product_id: int,
    payload: UpdateNameRequest,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(session)
    return await service.update_name(
        product_id=product_id,
        new_name=payload.name,
    )
    
    
# Endpoint to deactivate and reactivate a product

@router.patch(
    "/{product_id}/activate",
    response_model=ProductResponseSchema,
)
async def activate_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(session)
    return await service.activate_product(product_id)

@router.patch(
    "/{product_id}/deactivate",
    response_model=ProductResponseSchema,
)
async def deactivate_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(session)
    return await service.deactivate_product(product_id)

# Endpoint to add an image to a product
@router.post(
    "/{product_id}/images",
    response_model=ProductImageResponse,
)
async def add_product_image(
    product_id: int,
    payload: ProductImageCreate,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(session)
    return await service.add_product_image(
        product_id=product_id,
        image_url=payload.image_url,
    )
    
    
    
# Endpoint to soft delete a product 

@router.delete(
    "/{product_id}",
    response_model=ProductResponseSchema,
)
async def soft_delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
):
        service = ProductService(session)
        return await service.deactivate_product(product_id)