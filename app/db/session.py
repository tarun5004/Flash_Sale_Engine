from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker


from app.core.config import settings


#Crete async database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,    # Log SQL queries if in debug mode
    future=True,
)

#Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

#Dependency to get async database session for fastapi routes
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        
