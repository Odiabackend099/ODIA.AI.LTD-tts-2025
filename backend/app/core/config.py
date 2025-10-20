import os
from pydantic import BaseModel
from typing import Union

# Load environment variables from .env file
from dotenv import load_dotenv
import os

# Get the directory of this config.py file
config_dir = os.path.dirname(os.path.abspath(__file__))
# Go up three levels to reach the project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(config_dir)))
env_path = os.path.join(project_root, '.env')

print(f"DEBUG: Looking for .env file at: {env_path}")  # Debug print
if os.path.exists(env_path):
    load_dotenv(env_path)
    print("DEBUG: .env file loaded successfully")
else:
    print("DEBUG: .env file not found")

# Debug print to see what Redis URL is loaded
print(f"DEBUG: REDIS_URL from environment: {os.getenv('REDIS_URL', 'NOT_FOUND')}")

class Settings(BaseModel):
    PORT: int = int(os.getenv("PORT", 8000))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DIA_MODEL_ID: str = os.getenv("DIA_MODEL_ID", "nari-labs/Dia-1.6B")
    DIA_MODEL_REV: str = os.getenv("DIA_MODEL_REV", "main")
    HF_TOKEN: Union[str, None] = os.getenv("HF_TOKEN")
    MAX_CHARS: int = int(os.getenv("MAX_CHARS", "800"))
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

settings = Settings()
print(f"DEBUG: Settings.REDIS_URL: {settings.REDIS_URL}")  # Debug print