#!/bin/sh
set -e

# Ensure logs directory exists
mkdir -p /app/logs

# Start supervisord to manage Python API and Next.js
echo "Starting supervisord..."
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
