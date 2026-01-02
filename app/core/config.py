from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str ="flashsale-engine"
    DEBUG: bool = True
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    DATABASE_URL: str
    REDIS_URL: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
settings = Settings()