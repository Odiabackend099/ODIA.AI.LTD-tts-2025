from ..core.security import get_supabase_client

def log_usage(api_key: str, chars: int, duration_ms: int, cache_hit: bool):
    # Don't log if api_key is empty
    if not api_key:
        return
    supabase = get_supabase_client()
    supabase.table("usage_logs").insert({
        "api_key": api_key, "chars_used": chars, "duration_ms": duration_ms, "cache_hit": cache_hit
    }).execute()