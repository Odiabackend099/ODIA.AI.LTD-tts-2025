import os
import torch
import torchaudio
import tempfile
import uuid
from typing import Optional, Tuple
import numpy as np
from supabase import create_client
from ..core.config import settings

# Global variable to hold the speaker encoder
_ENC = None

def load_encoder():
    """Load the ECAPA-TDNN speaker encoder once at startup."""
    global _ENC
    if _ENC is None:
        try:
            from speechbrain.pretrained import SpeakerRecognition
            _ENC = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_ecapa"
            )
            print("Speaker encoder loaded successfully")
        except Exception as e:
            print(f"Error loading speaker encoder: {e}")
            _ENC = None
    return _ENC

def extract_embedding(audio_path: str) -> Optional[torch.Tensor]:
    """
    Extract 512-D embedding from audio file using ECAPA-TDNN.
    
    Args:
        audio_path: Path to audio file (WAV/MP3)
        
    Returns:
        512-D speaker embedding tensor or None if failed
    """
    try:
        enc = load_encoder()
        if enc is None:
            print("Speaker encoder not available")
            return None
            
        # Extract embedding
        emb = enc.encode_file(audio_path)
        return emb.squeeze(0)  # Remove batch dimension
    except Exception as e:
        print(f"Error extracting embedding: {e}")
        return None

def save_embedding_to_supabase(user_id: str, label: str, embedding: torch.Tensor) -> Optional[str]:
    """
    Save embedding to Supabase storage and metadata to database.
    
    Args:
        user_id: User identifier
        label: Voice profile label
        embedding: 512-D speaker embedding tensor
        
    Returns:
        Voice profile ID or None if failed
    """
    try:
        # Initialize Supabase client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        
        # Generate unique voice ID
        voice_id = str(uuid.uuid4())
        
        # Save embedding as .pt file
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp_file:
            torch.save(embedding, tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # Upload to Supabase Storage
            with open(tmp_path, "rb") as f:
                response = supabase.storage.from_("voices").upload(
                    file=f,
                    path=f"{user_id}/{voice_id}.pt",
                    file_options={"content-type": "application/octet-stream"}
                )
            
            # Save metadata to database
            data = {
                "user_id": user_id,
                "label": label,
                "path": f"{user_id}/{voice_id}.pt"
            }
            result = supabase.table("voice_profiles").insert(data).execute()
            
            if result.data:
                return voice_id
            else:
                print("Failed to save voice profile metadata")
                return None
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)
            
    except Exception as e:
        print(f"Error saving embedding to Supabase: {e}")
        return None

def load_embedding_from_supabase(user_id: str, voice_id: str) -> Optional[torch.Tensor]:
    """
    Load embedding from Supabase storage.
    
    Args:
        user_id: User identifier
        voice_id: Voice profile identifier
        
    Returns:
        512-D speaker embedding tensor or None if not found
    """
    try:
        # Initialize Supabase client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        
        # Download embedding file
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp_file:
            response = supabase.storage.from_("voices").download(f"{user_id}/{voice_id}.pt")
            tmp_file.write(response)
            tmp_path = tmp_file.name
        
        try:
            # Load embedding
            embedding = torch.load(tmp_path)
            return embedding
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)
            
    except Exception as e:
        print(f"Error loading embedding from Supabase: {e}")
        return None

def list_voice_profiles(user_id: str) -> list:
    """
    List available voice profiles for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        List of voice profile metadata
    """
    try:
        # Initialize Supabase client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        
        # Query voice profiles
        response = supabase.table("voice_profiles").select("*").eq("user_id", user_id).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error listing voice profiles: {e}")
        return []

def delete_voice_profile(user_id: str, voice_id: str) -> bool:
    """
    Delete a voice profile.
    
    Args:
        user_id: User identifier
        voice_id: Voice profile identifier
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize Supabase client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        
        # Delete from storage
        supabase.storage.from_("voices").remove([f"{user_id}/{voice_id}.pt"])
        
        # Delete from database
        supabase.table("voice_profiles").delete().eq("user_id", user_id).eq("id", voice_id).execute()
        
        return True
    except Exception as e:
        print(f"Error deleting voice profile: {e}")
        return False