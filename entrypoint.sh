#!/bin/sh
set -e

# Ensure Ollama home exists
mkdir -p /app/.ollama

# Ensure logs directory exists
mkdir -p /app/logs

# Start Ollama in background
echo "Starting Ollama server..."
OLLAMA_HOME=/app/.ollama ollama serve &

# Wait for Ollama to initialize
echo "Waiting for Ollama to be ready..."
sleep 10

# Pull the model
echo "Pulling AI model..."
OLLAMA_HOME=/app/.ollama ollama pull llama3.2:1b || true

# Start supervisord to manage Python API and Next.js
echo "Starting supervisord..."
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
