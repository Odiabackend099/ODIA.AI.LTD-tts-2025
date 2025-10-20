import os
import torch
import torchaudio
from typing import Union, Optional
import tempfile
import numpy as np
from .voice_clone import load_embedding_from_supabase

class VoiceCloningService:
    def __init__(self):
        # Load speaker encoder for voice cloning
        from .voice_clone import load_encoder
        load_encoder()
    
    def load_voice_profile(self, user_id: str, voice_id: str) -> Optional[torch.Tensor]:
        """
        Load voice profile from Supabase.
        
        Args:
            user_id: User identifier
            voice_id: Voice identifier
            
        Returns:
            Speaker embedding tensor or None if not found
        """
        try:
            # Use the voice_clone service to load embedding from Supabase
            embedding = load_embedding_from_supabase(user_id, voice_id)
            if embedding is not None:
                print(f"Voice profile loaded for user {user_id}, voice {voice_id}")
                return embedding
            else:
                print(f"Voice profile not found for user {user_id}, voice {voice_id}")
                return None
        except Exception as e:
            print(f"Error loading voice profile: {e}")
            return None

# Global instance
voice_service = VoiceCloningService()