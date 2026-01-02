from fastapi import FastAPI

from app.core.config import settings
from app.core.events import register_events

def create_app() -> FastAPI:
    """ 
    Application factory.
    Creates and configures FastAPI app.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG
    )
    
    register_events(app)
    
    return app




app = create_app()
    
    