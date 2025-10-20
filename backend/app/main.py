import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .routers import tts as tts_router
from .routers import voice as voice_router

app = FastAPI(title="ODIADEV-TTS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tts_router.router)
app.include_router(voice_router.router)

# Startup event to initialize services
@app.on_event("startup")
async def startup_event():
    # Initialize speaker encoder for voice cloning
    try:
        from .services.voice_clone import load_encoder
        load_encoder()
        print("Speaker encoder initialized")
    except Exception as e:
        print(f"Warning: Could not initialize speaker encoder: {e}")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=False)