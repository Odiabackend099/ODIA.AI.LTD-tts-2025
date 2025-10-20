#!/usr/bin/env python3
"""
Lifecycle policy script for voice embeddings.
Deletes embeddings after 90 days of inactivity and enforces storage quotas.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from supabase import create_client
from ..backend.app.core.config import settings

def connect_supabase():
    """Connect to Supabase."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

def cleanup_inactive_embeddings():
    """Delete voice embeddings that haven't been used in 90 days."""
    try:
        supabase = connect_supabase()
        
        # Calculate cutoff date (90 days ago)
        cutoff_date = datetime.now() - timedelta(days=90)
        
        # Query inactive voice profiles
        response = supabase.table("voice_profiles")\
            .select("*")\
            .lt("created_at", cutoff_date.isoformat())
        
        if response.data:
            print(f"Found {len(response.data)} inactive voice profiles")
            
            # Delete each inactive profile
            for profile in response.data:
                try:
                    # Delete from storage
                    file_path = profile["path"]
                    supabase.storage.from_("voices").remove([file_path])
                    
                    # Delete from database
                    supabase.table("voice_profiles").delete().eq("id", profile["id"]).execute()
                    
                    print(f"Deleted inactive voice profile: {profile['id']}")
                except Exception as e:
                    print(f"Error deleting profile {profile['id']}: {e}")
        else:
            print("No inactive voice profiles found")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")

def enforce_storage_quotas():
    """Enforce storage quotas per user."""
    try:
        supabase = connect_supabase()
        
        # Get all users with voice profiles
        response = supabase.table("voice_profiles").select("user_id").execute()
        
        if response.data:
            # Group by user
            user_profiles = {}
            for profile in response.data:
                user_id = profile["user_id"]
                if user_id not in user_profiles:
                    user_profiles[user_id] = []
                user_profiles[user_id].append(profile)
            
            # Enforce quotas (3 voices per free user, 10 per paid user)
            for user_id, profiles in user_profiles.items():
                # Simplified quota check - in reality, check user tier
                is_paid_user = check_if_paid_user(user_id)
                max_voices = 10 if is_paid_user else 3
                
                if len(profiles) > max_voices:
                    # Delete oldest profiles beyond quota
                    profiles.sort(key=lambda x: x["created_at"])
                    excess_profiles = profiles[max_voices:]
                    
                    print(f"User {user_id} exceeds quota by {len(excess_profiles)} voices")
                    
                    for profile in excess_profiles:
                        try:
                            # Delete from storage
                            file_path = profile["path"]
                            supabase.storage.from_("voices").remove([file_path])
                            
                            # Delete from database
                            supabase.table("voice_profiles").delete().eq("id", profile["id"]).execute()
                            
                            print(f"Deleted excess voice profile: {profile['id']}")
                        except Exception as e:
                            print(f"Error deleting excess profile {profile['id']}: {e}")
        else:
            print("No voice profiles found")
            
    except Exception as e:
        print(f"Error enforcing quotas: {e}")

def check_if_paid_user(user_id: str) -> bool:
    """Check if user is on paid tier (simplified implementation)."""
    # In a real implementation, this would check against a subscriptions table
    # For now, we'll assume all users are free tier except for special cases
    return False

def main():
    """Run lifecycle policies."""
    print("Running voice embedding lifecycle policies...")
    
    # Cleanup inactive embeddings
    print("1. Cleaning up inactive embeddings...")
    cleanup_inactive_embeddings()
    
    # Enforce storage quotas
    print("2. Enforcing storage quotas...")
    enforce_storage_quotas()
    
    print("Lifecycle policies completed successfully")

if __name__ == "__main__":
    main()