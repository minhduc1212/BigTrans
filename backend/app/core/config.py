import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Gibsnart API"
    API_V1_STR: str = "/api/v1"
    
    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 604800  # 7 days
    
    # Engine Settings
    DEFAULT_TIMEOUT: float = 8.0
    
    class Config:
        case_sensitive = True

settings = Settings()
