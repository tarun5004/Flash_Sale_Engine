"""
Auth Router — registration and login endpoints.
Layer: Router (thin — delegates all logic to UserService)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.user_service import UserService
from app.schemas.user_schema import (
    UserCreate,
    UserRead,
    LoginRequest,
    TokenResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    Flow: Router → UserService.register → UserRepository → DB
    """
    service = UserService(session)
    try:
        return await service.register(
            email=payload.email,
            password=payload.password,
        )
    except HTTPException:
        # Re-raise HTTP exceptions from service (409 duplicate, etc.)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return JWT.
    Flow: Router → UserService.login → verify password → create_access_token
    """
    service = UserService(session)
    # Service raises HTTPException (401/403) on failure — let it propagate
    return await service.login(
        email=payload.email,
        password=payload.password,
    )
