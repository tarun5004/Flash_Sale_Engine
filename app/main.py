from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.events import register_events
from app.routers.products import router as product_router
from app.routers.auth import router as auth_router
from app.routers.orders import router as order_router
from app.routers.cart import router as cart_router
from app.routers.seed import router as seed_router


def create_app() -> FastAPI:
    """ 
    Application factory.
    Creates and configures FastAPI app.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG
    )

    # CORS — allow frontend (served from file:// or different port) to call backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register startup/shutdown events
    register_events(app)

    # Register routers
    app.include_router(auth_router)
    app.include_router(product_router)
    app.include_router(order_router)
    app.include_router(cart_router)
    app.include_router(seed_router)

    # Serve frontend static files from project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app.mount("/static", StaticFiles(directory=project_root, html=True), name="static")

    return app


# Create FastAPI app instance
app = create_app()
