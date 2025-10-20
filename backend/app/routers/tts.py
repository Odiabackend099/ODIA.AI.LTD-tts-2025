import time
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Union
from ..core.security import validate_api_key
from ..services.dia import load_model, synthesize, synthesize_streaming
from ..services.cache import get_audio, set_audio
from ..services.voice import voice_service
from ..core.config import settings
from ..middleware.security import rate_limit_tts, log_request, add_watermark_for_free_tier, gpu_circuit_breaker
from fastapi.responses import Response, StreamingResponse

router = APIRouter()

# Metrics storage (in production, use Prometheus client)
_metrics = {
    "total_requests": 0,
    "cache_hits": 0,
    "total_latency": 0.0,  # Changed to float
    "error_count": 0
}

class TTSReq(BaseModel):
    text: str
    voice_id: Union[str, None] = None

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/metrics")
def metrics():
    """Expose metrics for monitoring."""
    if _metrics["total_requests"] > 0:
        avg_latency = _metrics["total_latency"] / _metrics["total_requests"]
        cache_hit_rate = _metrics["cache_hits"] / _metrics["total_requests"]
    else:
        avg_latency = 0.0
        cache_hit_rate = 0.0
    
    return {
        "total_requests": _metrics["total_requests"],
        "cache_hit_rate": cache_hit_rate,
        "average_latency": avg_latency,
        "error_count": _metrics["error_count"],
        "cache_hits": _metrics["cache_hits"]
    }

@router.get("/voices")
def list_voices(x_api_key: Union[str, None] = Header(None)):
    if not validate_api_key(x_api_key or ""):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # For now, return a static list
    # Later this will query Supabase for user's voices
    return {
        "available": ["base"],
        "custom": []
    }

@router.post("/tts")
@rate_limit_tts()
@log_request()
@add_watermark_for_free_tier()
@gpu_circuit_breaker()
def tts(req: TTSReq, request: Request, x_api_key: Union[str, None] = Header(None)):
    _metrics["total_requests"] += 1
    start_time = time.time()
    
    if not validate_api_key(x_api_key or ""):
        _metrics["error_count"] += 1
        raise HTTPException(status_code=401, detail="Invalid API key")
    text = (req.text or "").strip()
    if not text or len(text) > settings.MAX_CHARS:
        _metrics["error_count"] += 1
        raise HTTPException(status_code=400, detail=f"text is required and must be ≤ {settings.MAX_CHARS} chars")

    # Use enhanced cache key with model revision
    cached = get_audio(text, req.voice_id, settings.DIA_MODEL_REV)
    if cached:
        _metrics["cache_hits"] += 1
        duration_ms = int((time.time()-start_time)*1000)
        _metrics["total_latency"] += (time.time() - start_time)
        # Add watermark for free tier users if requested
        if hasattr(request.state, 'add_watermark') and request.state.add_watermark:
            # In a real implementation, we would add a watermark to the audio
            print("Adding watermark to cached audio for free tier user")
        return Response(content=cached, media_type="audio/mpeg")

    # Load speaker embedding if voice_id is provided
    speaker_embed = None
    if req.voice_id and req.voice_id != "base":
        # Extract user ID from API key (simplified for now)
        user_id = x_api_key or "default"
        speaker_embed = voice_service.load_voice_profile(user_id, req.voice_id)
    
    load_model(settings.DIA_MODEL_ID, settings.HF_TOKEN if settings.HF_TOKEN else None, settings.DIA_MODEL_REV)
    audio_mp3 = synthesize(text, speaker_embed=speaker_embed)
    
    # Add watermark for free tier users if requested
    if hasattr(request.state, 'add_watermark') and request.state.add_watermark:
        # In a real implementation, we would add a watermark to the audio
        print("Adding watermark to generated audio for free tier user")
    
    # Use enhanced cache key with model revision
    set_audio(text, req.voice_id, audio_mp3, settings.DIA_MODEL_REV)
    _metrics["total_latency"] += (time.time() - start_time)
    duration_ms = int((time.time()-start_time)*1000)
    return Response(content=audio_mp3, media_type="audio/mpeg")

@router.post("/tts/stream")
@rate_limit_tts()
@log_request()
@add_watermark_for_free_tier()
@gpu_circuit_breaker()
def tts_stream(req: TTSReq, request: Request, x_api_key: Union[str, None] = Header(None)):
    _metrics["total_requests"] += 1
    start_time = time.time()
    
    if not validate_api_key(x_api_key or ""):
        _metrics["error_count"] += 1
        raise HTTPException(status_code=401, detail="Invalid API key")
    text = (req.text or "").strip()
    if not text or len(text) > settings.MAX_CHARS:
        _metrics["error_count"] += 1
        raise HTTPException(status_code=400, detail=f"text is required and must be ≤ {settings.MAX_CHARS} chars")

    # Load speaker embedding if voice_id is provided
    speaker_embed = None
    if req.voice_id and req.voice_id != "base":
        # Extract user ID from API key (simplified for now)
        user_id = x_api_key or "default"
        speaker_embed = voice_service.load_voice_profile(user_id, req.voice_id)
    
    load_model(settings.DIA_MODEL_ID, settings.HF_TOKEN if settings.HF_TOKEN else None, settings.DIA_MODEL_REV)
    
    def generate():
        # Add watermark for free tier users if requested
        add_watermark = hasattr(request.state, 'add_watermark') and request.state.add_watermark
        if add_watermark:
            print("Adding watermark to streamed audio for free tier user")
        
        for chunk in synthesize_streaming(text, speaker_embed):
            yield chunk
    
    _metrics["total_latency"] += (time.time() - start_time)
    return StreamingResponse(generate(), media_type="audio/mpeg")