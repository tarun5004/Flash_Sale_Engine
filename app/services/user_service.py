"""
User Service — owns authentication business logic.
Layer: Service (between Router and Repository)
Responsibilities: registration validation, password hashing, credential verification, token creation.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user_schema import UserRead
# Security utilities live at project root — hashing + JWT
from security import hash_password, verify_password, create_access_token


class UserService:

    def __init__(self, session: AsyncSession):
        # Repository handles all DB access; service never touches session directly for queries
        self.session = session
        self.repo = UserRepository(session)

    async def register(self, email: str, password: str) -> UserRead:
        """
        Register a new user.
        Enforces email uniqueness at app layer before hitting a DB constraint.
        """
        # Check duplicates before insert — avoids exposing raw DB errors to the client
        existing = await self.repo.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Never store plaintext passwords — hash before persistence
        hashed = hash_password(password)

        user = User(
            email=email,
            hashed_password=hashed,
        )

        created_user = await self.repo.create(user)
        await self.session.commit()
        # Refresh to load server-generated fields (id, created_at)
        await self.session.refresh(created_user)

        return self._to_response(created_user)

    async def login(self, email: str, password: str) -> dict:
        """
        Verify credentials and return a JWT.
        Uses constant-time comparison via passlib to prevent timing attacks.
        """
        user = await self.repo.get_by_email(email)

        # Same error for "user not found" and "wrong password" — prevents email enumeration
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Inactive users are soft-blocked from the system
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        # Token payload uses "sub" (subject) claim — standard JWT convention
        token = create_access_token(data={"sub": str(user.id)})

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    @staticmethod
    def _to_response(user: User) -> UserRead:
        """ORM → Pydantic conversion — prevents MissingGreenlet outside async context."""
        return UserRead(
            id=user.id,
            email=user.email,
            is_active=bool(user.is_active),
            created_at=user.created_at,
        )
