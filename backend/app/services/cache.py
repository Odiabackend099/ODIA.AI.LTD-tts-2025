import hashlib, json, redis
from ..core.config import settings
from typing import Union

# Global variable to hold the Redis client
_r = None

def get_redis_client():
    global _r
    if _r is None:
        _r = redis.from_url(settings.REDIS_URL)
    return _r

def cache_key(text: str, voice_id: Union[str, None], model_rev: Union[str, None] = None, quality: str = "standard", sampler: str = "default"):
    """
    Generate cache key including all relevant parameters to prevent collisions.
    
    Args:
        text: Input text
        voice_id: Voice identifier (None for base voice)
        model_rev: Model revision (prevents collisions when model updates)
        quality: Audio quality setting
        sampler: Sampling method
    """
    m = hashlib.sha256()
    # Include all parameters that could affect the output
    key_string = "|".join([
        text.strip(),
        voice_id or "base",
        model_rev or settings.DIA_MODEL_REV or "main",
        quality,
        sampler
    ])
    m.update(key_string.encode())
    return "tts:" + m.hexdigest()

def get_audio(text: str, voice_id: Union[str, None], model_rev: Union[str, None] = None, quality: str = "standard", sampler: str = "default"):
    r = get_redis_client()
    return r.get(cache_key(text, voice_id, model_rev, quality, sampler))

def set_audio(text: str, voice_id: Union[str, None], audio_bytes: bytes, model_rev: Union[str, None] = None, quality: str = "standard", sampler: str = "default", ttl=86400):
    r = get_redis_client()
    # Set TTL to 24 hours as per specification for standard phrases
    # For large texts, consider shorter TTL (2 hours)
    actual_ttl = ttl if len(text) < 200 else min(ttl, 7200)  # 2 hours for long texts
    r.setex(cache_key(text, voice_id, model_rev, quality, sampler), actual_ttl, audio_bytes)