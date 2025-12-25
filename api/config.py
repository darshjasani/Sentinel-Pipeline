import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://ciuser:cipass@localhost:5432/ci_pipeline")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    log_base_path: str = "/app/logs"
    incident_threshold: int = 3  # Number of failures before creating incident
    flaky_test_min_runs: int = 5  # Minimum runs before considering flaky
    flaky_test_failure_range: tuple = (0.1, 0.9)  # Failure rate range for flaky tests

settings = Settings()

