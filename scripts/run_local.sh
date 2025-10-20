#!/bin/bash

# Exit on any error
set -e

echo "Starting ODIADEV-TTS services..."

# Start Redis in background
echo "Starting Redis..."
# Remove existing container if it exists
docker rm -f odia-redis 2>/dev/null || true
docker run -d --name odia-redis -p 6379:6379 redis:7-alpine

# Install backend dependencies
echo "Installing backend dependencies..."
cd ../backend
pip3 install -r requirements.txt

# Start backend
echo "Starting backend..."
python3 -m app.main &
BACKEND_PID=$!

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd ../frontend
npm install

# Start frontend
echo "Starting frontend..."
npm run dev &
FRONTEND_PID=$!

# Cleanup function
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    docker stop odia-redis 2>/dev/null || true
    docker rm odia-redis 2>/dev/null || true
    exit 0
}

# Set trap for cleanup on exit
trap cleanup EXIT INT TERM

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID