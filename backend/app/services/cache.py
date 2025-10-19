import hashlib, json, redis
from .config import settings

r = redis.from_url(settings.REDIS_URL)

def cache_key(text: str, voice_id: str | None):
    m = hashlib.sha256()
    m.update((text.strip() + "|" + (voice_id or "base")).encode())
    return "tts:" + m.hexdigest()

def get_audio(text: str, voice_id: str | None):
    return r.get(cache_key(text, voice_id))

def set_audio(text: str, voice_id: str | None, audio_bytes: bytes, ttl=86400):
    r.setex(cache_key(text, voice_id), ttl, audio_bytes)