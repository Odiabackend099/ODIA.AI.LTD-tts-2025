from supabase import create_client
from .config import settings

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

def log_usage(api_key: str, chars: int, duration_ms: int, cache_hit: bool):
    supabase.table("usage_logs").insert({
        "api_key": api_key, "chars_used": chars, "duration_ms": duration_ms, "cache_hit": cache_hit
    }).execute()