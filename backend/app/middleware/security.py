"""
Security middleware for rate limiting, consent capture, and request logging.
"""
import time
import uuid
import os
from typing import Optional
from fastapi import Request, HTTPException
from functools import wraps
from collections import defaultdict
from ..core.config import settings

# In-memory storage for rate limiting (replace with Redis in production)
_rate_limits = defaultdict(list)  # {api_key: [timestamp, ...]}
_consent_records = set()  # {api_key}

# Determine lane from environment
LANE = os.getenv("LANE", "priority")  # priority or free

# Rate limits per lane
if LANE == "priority":
    TTS_RATE_LIMIT = 120  # requests per minute for Pro/Biz
    CLONE_RATE_LIMIT = 5   # clones per day for Pro/Biz
else:  # free lane
    TTS_RATE_LIMIT = 30   # requests per minute for Free
    CLONE_RATE_LIMIT = 1  # clones per day for Free

def rate_limit_tts():
    """Rate limit TTS requests based on lane."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract API key from request
            request = kwargs.get('request') or (args[0] if args else None)
            if isinstance(request, Request):
                api_key = request.headers.get("X-API-Key")
                if api_key:
                    now = time.time()
                    # Clean old entries (older than 1 minute)
                    _rate_limits[api_key] = [ts for ts in _rate_limits[api_key] if now - ts < 60]
                    
                    # Check rate limit
                    if len(_rate_limits[api_key]) >= TTS_RATE_LIMIT:
                        raise HTTPException(
                            status_code=429,
                            detail=f"Rate limit exceeded: {TTS_RATE_LIMIT} TTS requests per minute",
                            headers={"Retry-After": "60"}
                        )
                    
                    # Add current request
                    _rate_limits[api_key].append(now)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit_clone():
    """Rate limit voice cloning based on lane."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract API key from request
            request = kwargs.get('request') or (args[0] if args else None)
            if isinstance(request, Request):
                api_key = request.headers.get("X-API-Key")
                if api_key:
                    now = time.time()
                    today = int(now // 86400)  # Unix day number
                    
                    # Clean old entries (older than 1 day)
                    cutoff = now - 86400
                    _rate_limits[api_key] = [ts for ts in _rate_limits[api_key] if ts > cutoff]
                    
                    # Count today's clones
                    today_clones = sum(1 for ts in _rate_limits[api_key] if int(ts // 86400) == today)
                    
                    # Check rate limit
                    if today_clones >= CLONE_RATE_LIMIT:
                        raise HTTPException(
                            status_code=429,
                            detail=f"Rate limit exceeded: {CLONE_RATE_LIMIT} voice clones per day",
                            headers={"Retry-After": "86400"}
                        )
                    
                    # Add current clone request
                    _rate_limits[api_key].append(now)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_consent():
    """Require consent for voice cloning operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract API key from request
            request = kwargs.get('request') or (args[0] if args else None)
            if isinstance(request, Request):
                api_key = request.headers.get("X-API-Key")
                if api_key and api_key not in _consent_records:
                    # Check if consent was provided in request
                    form_data = await request.form()
                    consent = form_data.get('consent')
                    if not consent or consent.lower() != 'true':
                        raise HTTPException(
                            status_code=400,
                            detail="Consent required: Please confirm you own the voice in the uploaded audio"
                        )
                    
                    # Record consent
                    _consent_records.add(api_key)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def log_request():
    """Log API requests for monitoring and abuse detection."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request details
            request = kwargs.get('request') or (args[0] if args else None)
            if isinstance(request, Request):
                api_key = request.headers.get("X-API-Key", "anonymous")
                endpoint = request.url.path
                method = request.method
                user_agent = request.headers.get("User-Agent", "")
                
                # Log request
                print(f"API Request: {method} {endpoint} | Key: {api_key} | UA: {user_agent} | Lane: {LANE}")
                
                # Add request ID for tracking
                request_id = str(uuid.uuid4())
                request.state.request_id = request_id
                
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                print(f"Request {request_id} completed in {duration:.3f}s | Lane: {LANE}")
                return result
            except Exception as e:
                duration = time.time() - start_time
                print(f"Request {request_id} failed after {duration:.3f}s: {e} | Lane: {LANE}")
                raise
        return wrapper
    return decorator

def add_watermark_for_free_tier():
    """Add watermark to audio for free tier users."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract API key from request
            request = kwargs.get('request') or (args[0] if args else None)
            if isinstance(request, Request):
                api_key = request.headers.get("X-API-Key")
                # Check if user is on free tier (simplified implementation)
                is_free_tier = api_key and not is_pro_user(api_key)
                
                # Always add watermark for free lane, optionally for free tier users in priority lane
                add_watermark = (LANE == "free") or (is_free_tier and LANE == "priority")
                
                if add_watermark:
                    # Add watermark flag to request state
                    request.state.add_watermark = True
                    print(f"Watermark will be added for request | Lane: {LANE}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def is_pro_user(api_key: str) -> bool:
    """Check if API key belongs to a pro user (simplified implementation)."""
    # In a real implementation, this would check against a database
    # For now, we'll assume test-key is free tier
    return api_key != "test-key"

# Circuit breaker for GPU overload protection
_gpu_util_history = []
_gpu_circuit_open = False

def gpu_circuit_breaker():
    """Circuit breaker for GPU overload protection."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            global _gpu_circuit_open
            
            # Check if circuit is open
            if _gpu_circuit_open:
                raise HTTPException(
                    status_code=429,
                    detail="Service temporarily unavailable due to high GPU load. Please try again later.",
                    headers={"Retry-After": "30"}
                )
            
            # Check GPU utilization (simplified - in real implementation, query nvidia-smi)
            # For now, we'll simulate with a random check
            import random
            gpu_util = random.randint(0, 100)
            _gpu_util_history.append(gpu_util)
            
            # Keep only last 10 readings
            if len(_gpu_util_history) > 10:
                _gpu_util_history.pop(0)
            
            # Calculate average GPU utilization
            avg_gpu_util = sum(_gpu_util_history) / len(_gpu_util_history) if _gpu_util_history else 0
            
            # Open circuit if GPU utilization is too high
            if avg_gpu_util > 90:
                _gpu_circuit_open = True
                print(f"GPU circuit breaker opened: avg utilization {avg_gpu_util:.1f}% | Lane: {LANE}")
                raise HTTPException(
                    status_code=429,
                    detail="Service temporarily unavailable due to high GPU load. Please try again later.",
                    headers={"Retry-After": "30"}
                )
            
            # Close circuit if GPU utilization is low
            if avg_gpu_util < 70:
                _gpu_circuit_open = False
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator