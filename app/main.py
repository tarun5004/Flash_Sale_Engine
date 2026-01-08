from fastapi import FastAPI

from app.core.config import settings
from app.core.events import register_events
from app.routers.products import router as product_router


def create_app() -> FastAPI:
    """ 
    Application factory.
    Creates and configures FastAPI app.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG
    )
    # Register startup/shutdown events
    register_events(app)
    # Register routers
    app.include_router(product_router)
    return app


# Create FastAPI app instance
app = create_app()
"""🔹 create_app() kya karta hai?
FastAPI() object banata hai
config apply karta hai
events register karta hai
routers attach karta hai
phir ready-to-use app return karta hai
👉 Is pattern ko kehte hain Application Factory Pattern"""
