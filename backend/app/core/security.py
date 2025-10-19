from supabase import create_client
from .config import settings

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

def validate_api_key(api_key: str) -> bool:
    if not api_key: return False
    data = supabase.table("api_keys").select("api_key,is_active").eq("api_key", api_key).execute()
    if not data.data: return False
    return bool(data.data[0].get("is_active", False))