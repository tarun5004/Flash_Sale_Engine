"""
Auth Dependencies — FastAPI dependency injection for authentication.
Layer: Core (shared across all routers that need auth)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from security import verify_access_token

# tokenUrl must match the login endpoint path — FastAPI uses this for Swagger UI's "Authorize" button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
):
    """
    Extracts user from JWT token.
    Injected as a dependency on any endpoint that requires authentication.
    Flow: Authorization header → token decode → user lookup → return user or 401
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        # WWW-Authenticate header required by OAuth2 spec on 401
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_access_token(token)
    except ValueError:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    repo = UserRepository(session)
    user = await repo.get_by_id(int(user_id_str))

    if user is None:
        raise credentials_exception

    # Block inactive users even if they have a valid token
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user
