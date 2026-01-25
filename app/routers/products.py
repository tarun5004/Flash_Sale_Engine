from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

# ✅ FIX: Removed unused import "from app.db import session"
# ❌ GALTI: "from app.db import session" use nahi ho raha tha
from app.db.session import get_db
from app.services.product_service import ProductService
from app.schemas.product_image_schema import ProductImageCreate, ProductImageResponse
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


# ==============================================
# CREATE PRODUCT
# ==============================================
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
    Flow: Request → Router → Service → Repository → DB
    """
    
    service = ProductService(session)  #service layer ka instance create karo mean ek session sabhi methods me use hoga
    
    try:
        # ✅ FIX: Service ab ProductResponseSchema return karti hai
        # Router ko bas directly return karna hai
        product = await service.create_product(
            name=payload.name,
            price=payload.price,
            stock=payload.stock,
        )
        # ✅ FIX: "return" → "return product"
        # ❌ GALTI: Empty return tha, client ko null milta
        return product
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==============================================
# UPDATE PRODUCT PRICE
# ==============================================
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
        # ✅ FIX: Ek baar call karo, result return karo
        # ❌ GALTI: Pehle 2 baar service.update_price() call ho raha tha
        product = await service.update_price(
            product_id=product_id,
            new_price=payload.price,
        )
        return product  # ← Direct return (already ProductResponseSchema)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================
# APPLY DISCOUNT
# ==============================================
@router.patch(
    "/{product_id}/discount",
    response_model=ProductResponseSchema,
)
async def apply_product_discount(
    product_id: int,
    payload: ProductApplyDiscountSchema,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(session)
    try:
        product = await service.apply_discount(
            product_id=product_id,
            discount_percent=payload.discount_percentage,
        )
        return product  # ← Direct return
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================
# GET PRODUCTS (with Pagination & Search)
# ==============================================
# ✅ FIX: Duplicate route remove kiya
# ❌ GALTI: @router.get("") 2 baar define tha (line 97 & 110)
# 📌 RULE: Same route path 2 baar define nahi kar sakte
@router.get(
    "",
    response_model=List[ProductResponseSchema],
)
async def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get all products with pagination and optional search.
    """
    service = ProductService(session)
    
    # ✅ Service already returns List[ProductResponseSchema]
    return await service.get_products(
        page=page,
        limit=limit,
        search=search,
    )


# ==============================================
# UPDATE STOCK
# ==============================================
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
    try:
        # ✅ Direct return - Service handles conversion
        return await service.update_stock(
            product_id=product_id,
            new_stock=payload.stock,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================
# UPDATE NAME
# ==============================================
class UpdateNameRequest(BaseModel):
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
    try:
        return await service.update_name(
            product_id=product_id,
            new_name=payload.name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================
# ACTIVATE PRODUCT
# ==============================================
@router.patch(
    "/{product_id}/activate",
    response_model=ProductResponseSchema,
)
async def activate_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(session)
    try:
        return await service.activate_product(product_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================
# DEACTIVATE PRODUCT
# ==============================================
@router.patch(
    "/{product_id}/deactivate",
    response_model=ProductResponseSchema,
)
async def deactivate_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(session)
    try:
        return await service.deactivate_product(product_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================
# ADD PRODUCT IMAGE
# ==============================================
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
    try:
        return await service.add_product_image(
            product_id=product_id,
            image_url=payload.image_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================
# SOFT DELETE PRODUCT
# ==============================================
@router.delete(
    "/{product_id}",
    response_model=ProductResponseSchema,
)
async def soft_delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Soft delete = is_active = False (product remains in DB)
    """
    service = ProductService(session)
    try:
        return await service.deactivate_product(product_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))