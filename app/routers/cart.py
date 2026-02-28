"""
Cart Router — auth-protected cart management endpoints.
Layer: Router (thin — delegates all logic to CartService)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.cart_service import CartService
from app.schemas.cart_schema import CartItemAdd, CartItemUpdate, CartItemRead, CartSummary

router = APIRouter(
    prefix="/cart",
    tags=["cart"],
)


@router.get(
    "",
    response_model=CartSummary,
)
async def get_cart(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Fetch the authenticated user's shopping cart."""
    service = CartService(session)
    return await service.get_cart(current_user.id)


@router.post(
    "",
    response_model=CartItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_to_cart(
    payload: CartItemAdd,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Add a product to the cart (or increment quantity if already present)."""
    service = CartService(session)
    try:
        return await service.add_item(
            user_id=current_user.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch(
    "/{item_id}",
    response_model=CartItemRead,
)
async def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Update quantity of a cart item."""
    service = CartService(session)
    try:
        return await service.update_item_quantity(
            user_id=current_user.id,
            item_id=item_id,
            quantity=payload.quantity,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Remove a specific item from the cart."""
    service = CartService(session)
    try:
        await service.remove_item(
            user_id=current_user.id,
            item_id=item_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Remove all items from the cart."""
    service = CartService(session)
    await service.clear_cart(current_user.id)
