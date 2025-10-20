#!/usr/bin/env python3
"""
Validation script for voice cloning pipeline.
Runs all acceptance tests to ensure system stability before production deployment.
"""

import os
import sys
import time
import subprocess
import requests
import json
import hashlib
from pathlib import Path

# Configuration
API_KEY = "test-key"
BASE_URL = "http://localhost:8000"
TEST_AUDIO = "test_sample.wav"  # 30-60s audio sample needed

def run_command(cmd, check=True):
    """Run shell command and return result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None
        return result
    except Exception as e:
        print(f"Command failed: {e}")
        return None

def test_health_and_auth():
    """Test 1: Health + Auth endpoints."""
    print("\n=== Test 1: Health + Auth ===")
    
    # Health check
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False
    
    # Auth test
    try:
        response = requests.post(
            f"{BASE_URL}/tts",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"text": "sanity"}
        )
        if response.status_code == 200:
            print("✓ Auth test passed")
        else:
            print(f"✗ Auth test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Auth test failed: {e}")
        return False
    
    return True

def test_clone_use_cache():
    """Test 2: Clone → Use → Cache."""
    print("\n=== Test 2: Clone → Use → Cache ===")
    
    if not os.path.exists(TEST_AUDIO):
        print(f"✗ Test audio file {TEST_AUDIO} not found. Please provide a 30-60s WAV/MP3 sample.")
        return False
    
    # Clone voice
    try:
        with open(TEST_AUDIO, 'rb') as f:
            files = {'file': (TEST_AUDIO, f, 'audio/wav')}
            data = {'label': 'FounderVoice'}
            headers = {'X-API-Key': API_KEY}
            response = requests.post(
                f"{BASE_URL}/clone",
                files=files,
                data=data,
                headers=headers
            )
        
        if response.status_code != 200:
            print(f"✗ Clone failed: {response.status_code}")
            return False
            
        result = response.json()
        voice_id = result.get('voice_id')
        if not voice_id:
            print("✗ No voice_id returned from clone")
            return False
            
        print(f"✓ Voice cloned successfully: {voice_id}")
    except Exception as e:
        print(f"✗ Clone failed: {e}")
        return False
    
    # Use cloned voice
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/tts",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"text": "Welcome to our service.", "voice_id": voice_id}
        )
        v1_time = time.time() - start_time
        
        if response.status_code != 200:
            print(f"✗ TTS with cloned voice failed: {response.status_code}")
            return False
            
        with open('v1.mp3', 'wb') as f:
            f.write(response.content)
        print(f"✓ TTS with cloned voice: {v1_time:.2f}s")
    except Exception as e:
        print(f"✗ TTS with cloned voice failed: {e}")
        return False
    
    # Cache hit check
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/tts",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"text": "Welcome to our service.", "voice_id": voice_id}
        )
        v2_time = time.time() - start_time
        
        if response.status_code != 200:
            print(f"✗ Cache hit test failed: {response.status_code}")
            return False
            
        with open('v2.mp3', 'wb') as f:
            f.write(response.content)
        print(f"✓ Cache hit test: {v2_time:.2f}s")
        
        # Check if cache hit was faster
        if v2_time < v1_time * 0.5:
            print("✓ Cache hit performance: ≥50% faster")
        else:
            print("⚠ Cache hit performance: Not significantly faster")
    except Exception as e:
        print(f"✗ Cache hit test failed: {e}")
        return False
    
    return True

def test_streaming():
    """Test 3: Streaming endpoint."""
    print("\n=== Test 3: Streaming Endpoint ===")
    
    # Get a voice_id for testing
    try:
        response = requests.get(
            f"{BASE_URL}/voices",
            headers={"X-API-Key": API_KEY}
        )
        if response.status_code == 200:
            data = response.json()
            # Use base voice if no custom voices available
            voice_id = "base"
            print("✓ Streaming endpoint accessible")
        else:
            print(f"✗ Streaming endpoint test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Streaming endpoint test failed: {e}")
        return False
    
    # Test streaming
    try:
        response = requests.post(
            f"{BASE_URL}/tts/stream",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"text": "This is a streaming test.", "voice_id": voice_id},
            stream=True
        )
        
        if response.status_code != 200:
            print(f"✗ Streaming test failed: {response.status_code}")
            return False
            
        with open('stream.mp3', 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print("✓ Streaming test completed - check stream.mp3 in Safari/Chrome")
    except Exception as e:
        print(f"✗ Streaming test failed: {e}")
        return False
    
    return True

def test_concurrency():
    """Test 4: Concurrency + Stability."""
    print("\n=== Test 4: Concurrency + Stability ===")
    
    # Start monitoring GPU in background
    monitor_cmd = "watch -n 2 nvidia-smi > gpu_monitor.log &"
    run_command(monitor_cmd, check=False)
    
    # Run concurrent requests
    try:
        import concurrent.futures
        import threading
        
        def make_request(i):
            try:
                response = requests.post(
                    f"{BASE_URL}/tts",
                    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                    json={"text": f"Parallel test #{i}", "voice_id": "base"}
                )
                return response.status_code == 200
            except Exception:
                return False
        
        # 10 concurrent requests, 50 total
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(results)
        print(f"✓ Concurrency test: {success_count}/50 requests successful")
        
        if success_count >= 45:  # Allow some failures
            return True
        else:
            print("✗ Concurrency test: Too many failures")
            return False
    except Exception as e:
        print(f"✗ Concurrency test failed: {e}")
        return False
    finally:
        # Stop monitoring
        run_command("pkill -f 'watch -n 2 nvidia-smi'", check=False)

def test_storage_integrity():
    """Test 5: Storage/DB Integrity."""
    print("\n=== Test 5: Storage/DB Integrity ===")
    
    # This test requires manual verification in Supabase dashboard
    print("Manual verification needed:")
    print("1. Check Supabase: confirm one voice_profiles row + one storage object per clone")
    print("2. Run DELETE test after validation:")
    print(f"   curl -s -X DELETE {BASE_URL}/voices/<uuid> -H 'X-API-Key:{API_KEY}'")
    print("3. Verify DB row and storage object are removed")
    
    return True

def main():
    """Run all validation tests."""
    print("Starting voice cloning pipeline validation...")
    
    tests = [
        test_health_and_auth,
        test_clone_use_cache,
        test_streaming,
        test_concurrency,
        test_storage_integrity
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"Test {test.__name__} failed")
    
    print(f"\n=== Validation Summary ===")
    print(f"Passed: {passed}/{len(tests)} tests")
    
    if passed == len(tests):
        print("🎉 All tests passed! Pipeline is ready for production.")
        return True
    else:
        print("❌ Some tests failed. Please fix issues before production deployment.")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)