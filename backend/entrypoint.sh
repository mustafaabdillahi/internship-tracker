#!/bin/sh

if [ "$PRODUCTION" = "true" ]; then
    echo "Starting in production mode..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port "${PORT:-8000}"
else
    echo "Starting in development mode..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload
fi