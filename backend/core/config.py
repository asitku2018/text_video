import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB limit to prevent DDoS via large files
    ALLOWED_IMAGE_TYPES: set = {"image/jpeg", "image/png", "image/webp"}

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
