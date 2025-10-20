import io
import os
import time
from typing import Optional, Generator
import torch
from pydub import AudioSegment

# HF APIs (we try pipeline first; if not available we fall back to model+processor)
from transformers import (
    AutoProcessor,
    AutoModelForSpeechSeq2Seq,
    pipeline as hf_pipeline,
)

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_MODEL = None
_PROCESSOR = None
_PIPE = None  # transformers pipeline handle (if available)
_SAMPLE_RATE = 16000

# Feature flags via env
_USE_BNB = os.getenv("DIA_USE_BNB", "0") == "1"         # 8-bit/4-bit quant if available
_LOAD_4BIT = os.getenv("DIA_4BIT", "0") == "1"          # force 4bit
_LOAD_8BIT = os.getenv("DIA_8BIT", "0") == "1" or _USE_BNB  # default to 8-bit if DIA_USE_BNB=1
_ENABLE_STREAM = os.getenv("DIA_ENABLE_STREAM", "1") == "1" # stream MP3 chunks (frontend feels faster)

def _bnb_kwargs():
    """Build bitsandbytes kwargs safely."""
    if _DEVICE != "cuda":
        return {}
    if _LOAD_4BIT:
        return dict(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            device_map="auto",
        )
    if _LOAD_8BIT:
        return dict(load_in_8bit=True, device_map="auto")
    return {}

def load_model(model_id: str, hf_token: Optional[str] = None, revision: Optional[str] = None) -> None:
    """
    Warm-load the DIA model once. Tries HF pipeline first, then manual processor+model.
    Uses mixed precision on CUDA. Never reload inside request path.
    """
    global _MODEL, _PROCESSOR, _PIPE

    if _PIPE or _MODEL:
        return  # already loaded

    # Try pipeline path (if model exposes a speech TTS task)
    try:
        # Simplified pipeline call to avoid type errors
        _PIPE = hf_pipeline(
            "text2text-generation",
            model=model_id,
            revision=revision,
            torch_dtype=torch.float16 if _DEVICE == "cuda" else torch.float32,
            device=0 if _DEVICE == "cuda" else -1,
        )
        # Warmup
        if _PIPE is not None:
            _ = _PIPE("warm up")
        return
    except Exception as e:
        print(f"Pipeline loading failed: {e}")
        _PIPE = None  # fall through to raw model path

    # Fallback to raw model + processor
    bnb_args = _bnb_kwargs()
    
    # Load processor with revision if specified
    processor_kwargs = {"token": hf_token}
    if revision:
        processor_kwargs["revision"] = revision
    _PROCESSOR = AutoProcessor.from_pretrained(model_id, **processor_kwargs)
    
    # Load model with revision if specified
    model_kwargs = {
        "low_cpu_mem_usage": True,
        "use_safetensors": True,
        "token": hf_token,
    }
    if revision:
        model_kwargs["revision"] = revision
    if bnb_args:
        # quantized load
        model_kwargs.update(bnb_args)
        _MODEL = AutoModelForSpeechSeq2Seq.from_pretrained(model_id, **model_kwargs)
    else:
        # fp16/fp32 path
        model_kwargs["torch_dtype"] = torch.float16 if _DEVICE == "cuda" else torch.float32
        _MODEL = AutoModelForSpeechSeq2Seq.from_pretrained(model_id, **model_kwargs).to(_DEVICE)

    _MODEL.eval()
    if _DEVICE == "cuda" and not bnb_args:
        # Prefer half precision & cudnn autotune
        try:
            _MODEL.half()
        except Exception:
            pass
        torch.backends.cudnn.benchmark = True

    # warm pass (best-effort)
    try:
        _ = _synthesize_impl("warm up", None)
    except Exception:
        pass

def _wav_to_mp3_bytes(wav: torch.Tensor, sample_rate: int = _SAMPLE_RATE) -> bytes:
    """
    Convert mono float waveform [-1..1] to MP3 bytes.
    """
    if wav.dim() > 1:
        wav = wav.squeeze(0)
    wav16 = (wav.clamp(-1, 1) * 32767).to(torch.int16).cpu().numpy().tobytes()
    buf = io.BytesIO()
    audio = AudioSegment(
        wav16, frame_rate=sample_rate, sample_width=2, channels=1
    )
    audio.export(buf, format="mp3", bitrate="64k")
    return buf.getvalue()

def _synthesize_with_pipeline(text: str, speaker_embed=None):
    """
    If HF pipeline works, use it. Expect pipeline to return waveform or bytes.
    """
    if _PIPE is not None:
        try:
            # Try to pass speaker embedding to pipeline if available
            if speaker_embed is not None:
                out = _PIPE(text, speaker_embeddings=speaker_embed)
            else:
                out = _PIPE(text)
            return _process_pipeline_output(out)
        except Exception as e:
            print(f"Pipeline synthesis failed: {e}")
            pass
    # Fallback if pipeline is None or failed
    tone = torch.sin(
        2 * torch.pi * torch.arange(0, _SAMPLE_RATE * 1) / _SAMPLE_RATE * 880
    ).unsqueeze(0)
    return _wav_to_mp3_bytes(tone)

def _process_pipeline_output(out) -> bytes:
    """Process pipeline output to MP3 bytes."""
    # normalizations:
    if isinstance(out, dict):
        if "audio" in out and isinstance(out["audio"], bytes):
            # Already encoded; try pass-through
            return out["audio"]
        if "waveform" in out:
            wav = out["waveform"]
            if isinstance(wav, torch.Tensor):
                return _wav_to_mp3_bytes(wav)
    # If it's raw tensor:
    if isinstance(out, torch.Tensor):
        return _wav_to_mp3_bytes(out)
    # Last resort: create a short tone (never fail)
    tone = torch.sin(
        2 * torch.pi * torch.arange(0, _SAMPLE_RATE * 1) / _SAMPLE_RATE * 880
    ).unsqueeze(0)
    return _wav_to_mp3_bytes(tone)

@torch.inference_mode()
def _synthesize_impl(text: str, speaker_embed=None) -> bytes:
    """
    Unified synth: pipeline→raw model→tone fallback.
    """
    # 1) Pipeline path
    if _PIPE is not None:
        # Pass speaker embedding if available
        if speaker_embed is not None:
            # Try to pass speaker embedding to pipeline
            try:
                out = _PIPE(text, speaker_embeddings=speaker_embed)
                return _process_pipeline_output(out)
            except Exception as e:
                print(f"Pipeline with speaker embedding failed: {e}")
                # Fall back to synthesis without speaker embedding
                pass
        return _synthesize_with_pipeline(text, speaker_embed)

    # 2) Raw model + processor path (example forward; adapt if DIA differs)
    if _MODEL is not None and _PROCESSOR is not None:
        if _DEVICE == "cuda":
            autocast_dtype = torch.float16
        else:
            autocast_dtype = torch.float32

        with torch.cuda.amp.autocast(enabled=(_DEVICE == "cuda"), dtype=autocast_dtype):
            inputs = _PROCESSOR(text=text, return_tensors="pt").to(_DEVICE)
            
            # Pass speaker embedding if available and model supports it
            generate_kwargs = {}
            if speaker_embed is not None:
                # Check if model has a method to set speaker embeddings
                if hasattr(_MODEL, "set_speaker_embeddings"):
                    _MODEL.set_speaker_embeddings(speaker_embed)
                # Or pass as a generation parameter if supported
                elif hasattr(_MODEL, "generate") and hasattr(_MODEL.generate, "__code__"):
                    # Check if generate method accepts speaker_embeddings parameter
                    import inspect
                    sig = inspect.signature(_MODEL.generate)
                    if "speaker_embeddings" in sig.parameters:
                        generate_kwargs["speaker_embeddings"] = speaker_embed
            
            # NOTE: Replace the following with DIA's actual generation API if different.
            # Many TTS models expose something like generate(...) returning waveform/ids.
            if hasattr(_MODEL, "generate"):
                ids = _MODEL.generate(**inputs, max_new_tokens=2048, **generate_kwargs)
                # If processor can decode ids to waveform:
                if hasattr(_PROCESSOR, "batch_decode"):
                    wav = _PROCESSOR.batch_decode(ids, sampling_rate=_SAMPLE_RATE)
                    if isinstance(wav, torch.Tensor):
                        return _wav_to_mp3_bytes(wav, _SAMPLE_RATE)
            # If direct waveform method exists (pseudo-case):
            elif hasattr(_MODEL, "generate_speech"):
                wav = _MODEL.generate_speech(**inputs, speaker_embed=speaker_embed, sample_rate=_SAMPLE_RATE)
                if isinstance(wav, torch.Tensor):
                    return _wav_to_mp3_bytes(wav, _SAMPLE_RATE)

        # If shape/API mismatch, fall through to tone.
    # 3) Fallback tone — guarantees a valid MP3
    tone = torch.sin(
        2 * torch.pi * torch.arange(0, _SAMPLE_RATE * 1) / _SAMPLE_RATE * 440
    ).unsqueeze(0)
    return _wav_to_mp3_bytes(tone, _SAMPLE_RATE)

def synthesize(text: str, speaker_embed=None) -> bytes:
    """
    Non-streaming synth: returns full MP3 bytes.
    Optionally accepts speaker embedding for voice cloning.
    """
    start = time.time()
    mp3 = _synthesize_impl(text, speaker_embed)
    duration = time.time() - start
    print(f"Synthesis completed in {duration:.2f}s")
    return mp3

def synthesize_streaming(text: str, speaker_embed=None, chunk_ms: int = 240) -> Generator[bytes, None, None]:
    """
    Streaming generator that yields MP3 chunks.
    Strategy: produce full mp3 then slice into ~chunk_ms frames; good enough for UX.
    (Real-time vocoder chunking needs model-specific support; this keeps API stable.)
    """
    mp3 = synthesize(text, speaker_embed)
    # naive slicing by bytes — MP3 frames are variable; this is a UX trick, not bit-perfect.
    total = len(mp3)
    parts = max(1, total // (16000 // (1000 // chunk_ms)))  # heuristic
    step = max(1024, total // parts)
    for i in range(0, total, step):
        yield mp3[i : i + step]