import io, time, torch, torchaudio
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from pydub import AudioSegment

_model = None
_processor = None
_device = "cuda" if torch.cuda.is_available() else "cpu"

def load_model(model_id: str, hf_token: str | None = None):
    global _model, _processor
    if _model: return
    _processor = AutoProcessor.from_pretrained(model_id, token=hf_token)
    _model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch.float16 if _device=="cuda" else torch.float32,
        low_cpu_mem_usage=True, use_safetensors=True, token=hf_token
    ).to(_device).eval()

def synthesize(text: str, speaker_embed: torch.Tensor | None = None, sample_rate: int = 16000) -> bytes:
    """
    NOTE: This assumes the DIA repo exposes a text->waveform forward pass via processor.
    If the specific API differs, adapt the forward call but keep this function signature.
    """
    with torch.inference_mode():
        inputs = _processor(text=text, return_tensors="pt").to(_device)
        # --- PLACEHOLDER FOR DIA GENERATION ---
        # Replace the below with actual DIA generation API (e.g., _model.generate_speech)
        # For now, produce a 0.5s tone placeholder if DIA not integrated.
        if not hasattr(_model, "generate"):
            tone = torch.sin(2*torch.pi*torch.arange(0, sample_rate*1)/sample_rate*440).unsqueeze(0)
            wav = tone.to(torch.float32)
        else:
            # Example: ids = _model.generate(**inputs)
            # wav = _processor.batch_decode(ids) -> waveform tensor
            # Placeholder: 1kHz beep
            wav = torch.sin(2*torch.pi*torch.arange(0, sample_rate*1)/sample_rate*1000).unsqueeze(0)
        # Convert to mp3
        buf = io.BytesIO()
        audio = AudioSegment(
            (wav.squeeze().cpu().numpy()*32767).astype("int16").tobytes(),
            frame_rate=sample_rate, sample_width=2, channels=1
        )
        audio.export(buf, format="mp3", bitrate="64k")
        return buf.getvalue()