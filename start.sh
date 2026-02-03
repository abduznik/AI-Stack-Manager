#!/bin/bash

# Ensure workspace directory exists
mkdir -p /app/workspace

echo "[INIT] Starting Server..."
exec uvicorn app.server:app --host 0.0.0.0 --port 8090