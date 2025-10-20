#!/bin/bash
# Start Free Lane Service

echo "Starting Free Lane Service (Port 8001)..."
echo "Lane: Free | Max Concurrent: 1 | Watermark: ON"

# Load free environment
export ENV_FILE="/workspace/infra/env.free"

# Start without --reload for production
cd /workspace/backend
uvicorn app.main:app --host 0.0.0.0 --port 8001 --env-file $ENV_FILE

echo "Free Lane Service stopped."