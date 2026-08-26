#!/bin/sh
set -e

if [ "$PRODUCTION" = "true" ]; then
    echo "Checking database..."
    if alembic current 2>&1 | grep -q "No current revision"; then
        echo "Database has no Alembic revision. Generating initial migration..."
        alembic revision --autogenerate -m "initial migration"
        
        echo "Applying initial migration..."
        alembic upgrade head
    else
        echo "Running database migrations..."
        alembic upgrade head
    fi
    
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