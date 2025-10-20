#!/usr/bin/env python3
"""
Deployment script for RunPod.
Prepares and deploys the ODIADEV-TTS service to RunPod with AIDA-2000 GPU.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# RunPod API configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_API_URL = "https://api.runpod.io/v2"

# Deployment configuration
DEPLOYMENT_CONFIG = {
    "name": "odia-tts-service",
    "image": "python:3.11",
    "gpu_type": "AIDA-2000",  # Start with AIDA-2000
    "gpu_count": 1,
    "container_disk_in_gb": 50,
    "volume_mount_path": "/workspace",
    "ports": "8000/http",
    "env": {
        "PORT": "8000",
        "LOG_LEVEL": "INFO",
        "REDIS_URL": "redis://localhost:6379/0",
        "DIA_MODEL_ID": "nari-labs/Dia-1.6B",
        "DIA_MODEL_REV": "main",
        "MAX_CHARS": "800",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "NEXT_PUBLIC_API_BASE": "http://localhost:8000"
    },
    "start_command": "cd /workspace && pip install -r requirements.txt && python -m app.main"
}

def check_runpod_api_key():
    """Check if RunPod API key is available."""
    if not RUNPOD_API_KEY:
        print("Error: RUNPOD_API_KEY environment variable not set")
        print("Please set it with: export RUNPOD_API_KEY=your_api_key")
        return False
    return True

def create_pod():
    """Create a new pod on RunPod."""
    if not check_runpod_api_key():
        return None
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Add Supabase credentials if available
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_url and supabase_key:
        DEPLOYMENT_CONFIG["env"]["SUPABASE_URL"] = supabase_url
        DEPLOYMENT_CONFIG["env"]["SUPABASE_SERVICE_ROLE_KEY"] = supabase_key
    
    payload = {
        "input": {
            "deployment": DEPLOYMENT_CONFIG
        }
    }
    
    try:
        response = requests.post(
            f"{RUNPOD_API_URL}/run",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            pod_id = result.get("id")
            print(f"Pod created successfully: {pod_id}")
            return pod_id
        else:
            print(f"Error creating pod: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error creating pod: {e}")
        return None

def deploy_to_runpod():
    """Deploy the service to RunPod."""
    print("Deploying ODIADEV-TTS to RunPod...")
    
    # Create pod
    pod_id = create_pod()
    if not pod_id:
        print("Failed to create pod")
        return False
    
    print(f"Pod {pod_id} created. Waiting for deployment...")
    
    # Wait for pod to be ready
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        if check_pod_status(pod_id):
            print("Pod is ready!")
            print(f"Service available at: https://api.runpod.io/v2/{pod_id}/runsync")
            return True
        time.sleep(10)
    
    print("Timeout waiting for pod to be ready")
    return False

def check_pod_status(pod_id):
    """Check if pod is ready."""
    if not check_runpod_api_key():
        return False
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    try:
        response = requests.get(
            f"{RUNPOD_API_URL}/{pod_id}/status",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "")
            return status == "RUNNING"
        return False
    except Exception as e:
        print(f"Error checking pod status: {e}")
        return False

def setup_autoscaling():
    """Setup autoscaling to A10G when needed."""
    print("Setting up autoscaling policies...")
    print("Note: This would be configured in the RunPod dashboard")
    print("- Scale up to A10G when p95 latency > 5s for 12-15s audio")
    print("- Scale down to AIDA-2000 during low usage periods")
    return True

def main():
    """Main deployment function."""
    print("ODIADEV-TTS RunPod Deployment")
    print("=" * 40)
    
    # Deploy to RunPod
    if deploy_to_runpod():
        print("\n✓ Deployment successful!")
        print("Next steps:")
        print("1. Test the service with sample requests")
        print("2. Setup autoscaling policies")
        print("3. Configure monitoring and alerts")
        print("4. Setup domain and SSL certificates")
        return True
    else:
        print("\n✗ Deployment failed!")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)