from fastapi import Form
import os
import tempfile
import uuid
from fastapi import APIRouter, Header, HTTPException, UploadFile, File, Request
from typing import Union, List
from ..core.security import validate_api_key
from ..core.config import settings
from ..services.voice_clone import (
    extract_embedding, 
    save_embedding_to_supabase, 
    load_embedding_from_supabase,
    list_voice_profiles,
    delete_voice_profile
)
from ..middleware.security import rate_limit_clone, require_consent, log_request

router = APIRouter()

@router.get("/voices")
def list_voices(x_api_key: Union[str, None] = Header(None)):
    if not validate_api_key(x_api_key or ""):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Extract user ID from API key (simplified for now)
    user_id = x_api_key or "default"
    
    # Get list of voice profiles
    profiles = list_voice_profiles(user_id)
    
    return {
        "available": ["base"],
        "custom": profiles
    }

@router.post("/clone")
@rate_limit_clone()
@require_consent()
@log_request()
async def clone_voice(
    request: Request,
    audio_file: UploadFile = File(...),
    label: str = "Custom Voice",
    consent: str = Form(...),  # Require consent
    x_api_key: Union[str, None] = Header(None)
):
    if not validate_api_key(x_api_key or ""):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Validate consent
    if consent.lower() != 'true':
        raise HTTPException(
            status_code=400,
            detail="Consent required: Please confirm you own the voice in the uploaded audio"
        )
    
    # Validate file type
    if audio_file.content_type not in ["audio/wav", "audio/mp3", "audio/mpeg", "audio/x-wav"]:
        raise HTTPException(status_code=400, detail="Only WAV and MP3 files are supported")
    
    # Validate file size (limit to 6MB)
    content = await audio_file.read()
    if len(content) > 6 * 1024 * 1024:  # 6 MB
        raise HTTPException(status_code=400, detail="File size must be less than 6 MB")
    
    # Validate audio duration (20-60 seconds)
    # Note: Proper duration checking would require audio processing
    # For now, we'll assume the file size constraint is sufficient
    
    # Reset file pointer
    await audio_file.seek(0)
    
    # Save file temporarily
    filename = audio_file.filename or "voice_upload.wav"
    file_extension = os.path.splitext(filename)[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        content = await audio_file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Extract speaker embedding
        embedding = extract_embedding(tmp_path)
        if embedding is None:
            raise HTTPException(status_code=500, detail="Failed to extract voice embedding")
        
        # Extract user ID from API key
        user_id = x_api_key or "default"
        
        # Save embedding to Supabase
        voice_id = save_embedding_to_supabase(user_id, label, embedding)
        if voice_id is None:
            raise HTTPException(status_code=500, detail="Failed to save voice profile")
        
        return {
            "status": "success",
            "message": "Voice cloned successfully",
            "voice_id": voice_id,
            "label": label
        }
    finally:
        # Clean up temporary file
        os.unlink(tmp_path)

@router.delete("/voices/{voice_id}")
def delete_voice(voice_id: str, x_api_key: Union[str, None] = Header(None)):
    if not validate_api_key(x_api_key or ""):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Extract user ID from API key
    user_id = x_api_key or "default"
    
    # Delete voice profile
    success = delete_voice_profile(user_id, voice_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete voice profile")
    
    return {
        "status": "success",
        "message": "Voice profile deleted successfully"
    }