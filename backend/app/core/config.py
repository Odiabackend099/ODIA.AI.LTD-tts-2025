import os
from pydantic import BaseModel

class Settings(BaseModel):
    PORT: int = int(os.getenv("PORT", 8000))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DIA_MODEL_ID: str = os.getenv("DIA_MODEL_ID", "nari-labs/Dia-1.6B")
    HF_TOKEN: str | None = os.getenv("HF_TOKEN")
    MAX_CHARS: int = int(os.getenv("MAX_CHARS", "800"))
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

settings = Settings()