import time
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from ..core.security import validate_api_key
from ..services.dia import load_model, synthesize
from ..services.cache import get_audio, set_audio
from ..services.usage import log_usage
from ..core.config import settings
from fastapi.responses import Response

router = APIRouter()

class TTSReq(BaseModel):
    text: str
    voice_id: str | None = None

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/tts")
def tts(req: TTSReq, x_api_key: str | None = Header(None)):
    if not validate_api_key(x_api_key or ""):
        raise HTTPException(status_code=401, detail="Invalid API key")
    text = (req.text or "").strip()
    if not text or len(text) > settings.MAX_CHARS:
        raise HTTPException(status_code=400, detail=f"text is required and must be <= {settings.MAX_CHARS} chars")

    start = time.time()
    cached = get_audio(text, req.voice_id)
    if cached:
        duration_ms = int((time.time()-start)*1000)
        log_usage(x_api_key, len(text), duration_ms, True)
        return Response(content=cached, media_type="audio/mpeg")

    load_model(settings.DIA_MODEL_ID, settings.HF_TOKEN)
    audio_mp3 = synthesize(text, speaker_embed=None)
    set_audio(text, req.voice_id, audio_mp3)
    duration_ms = int((time.time()-start)*1000)
    log_usage(x_api_key, len(text), duration_ms, False)
    return Response(content=audio_mp3, media_type="audio/mpeg")