#!/bin/sh
# Preview launcher: uses the venv uvicorn and the proxy-provided $PORT.
cd "$(dirname "$0")"
exec ../.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
