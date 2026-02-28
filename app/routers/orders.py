"""
Order Router — order placement & history endpoints (auth-protected).
Layer: Router (thin — delegates all logic to OrderService)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.order_service import OrderService
from app.schemas.order_schema import OrderCreate, OrderRead

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


@router.get(
    "",
    response_model=List[OrderRead],
)
async def get_orders(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Fetch all orders for the authenticated user."""
    service = OrderService(session)
    return await service.get_user_orders(current_user.id)


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Place a new order.
    Flow: JWT → get_current_user → OrderService.create_order → lock stock → payment → response
    """
    service = OrderService(session)
    try:
        return await service.create_order(
            user_id=current_user.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
