#!/bin/bash
# Start Priority Lane (Pro/Biz) Service

echo "Starting Priority Lane Service (Port 8000)..."
echo "Lane: Priority | Max Concurrent: 2 | Watermark: OFF"

# Load priority environment
export ENV_FILE="/workspace/infra/env.priority"

# Start without --reload for production
cd /workspace/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-file $ENV_FILE

echo "Priority Lane Service stopped."