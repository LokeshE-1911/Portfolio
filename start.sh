#!/usr/bin/env bash
set -e

# Uvicorn tuned for cold-starts
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-10001}" \
  --workers 1 \
  --timeout-keep-alive 120
