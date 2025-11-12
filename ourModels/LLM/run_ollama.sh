#!/bin/bash
set -e

PORT=$1
MODEL=$2

if [ -z "$PORT" ] || [ -z "$MODEL" ]; then
  echo "Usage: $0 <port> <model-name>"
  exit 1
fi

# Run Ollama container
echo "Starting Ollama container on port $PORT..."
CID=$(docker run -d -p ${PORT}:11434 ollama/ollama)

echo "Container started: $CID"

# Wait a bit for Ollama to initialize
sleep 5

# Pull the specified model
echo "Pulling model: $MODEL"
docker exec "$CID" ollama pull "$MODEL"

echo "✅ Model '$MODEL' pulled successfully in container: $CID"
echo "🌐 Accessible on $PORT"
