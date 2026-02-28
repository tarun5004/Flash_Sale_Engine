from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base

# Models must be imported before create_all — registers them with Base.metadata
from app.models.product import Product  # noqa: F401
from app.models.product_image import ProductImage  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.cart_item import CartItem  # noqa: F401


def register_events(app: FastAPI) -> None:
    """Register event handlers for the FastAPI application."""

    @app.on_event("startup")
    async def startup_event():
        # Initialize DB: create tables (if any) and ensure DB file exists
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # TODO: initialize cache, celery, other services
        print("Application startup")

    @app.on_event("shutdown")
    async def shutdown_event():
        # TODO: close database, redis connections
        print("Application shutdown")