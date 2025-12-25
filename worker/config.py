import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://ciuser:cipass@localhost:5432/ci_pipeline")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    log_base_path: str = "/app/logs"

settings = Settings()

