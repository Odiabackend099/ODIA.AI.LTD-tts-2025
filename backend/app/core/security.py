import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Global variable to hold the Supabase client
_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        print(f"Supabase URL: {supabase_url}")
        print(f"Supabase Key: {supabase_key[:10]}...")  # Print first 10 characters of the key for debugging
        _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client

def validate_api_key(api_key: str) -> bool:
    if not api_key: 
        print("No API key provided")
        return False
    supabase = get_supabase_client()
    print(f"Validating API key: {api_key}")
    try:
        data = supabase.table("api_keys").select("api_key,is_active").eq("api_key", api_key).execute()
        print(f"Query result: {data}")
        if not data.data: 
            print("No data returned from query")
            return False
        print(f"API key found: {data.data[0]}")
        return bool(data.data[0].get("is_active", False))
    except Exception as e:
        print(f"Error validating API key: {e}")
        return False