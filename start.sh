#!/bin/bash

# Exit on any error
set -e

echo "=== STARTUP SCRIPT STARTED ==="
echo "Timestamp: $(date)"
echo "Environment: $ENVIRONMENT"
echo "Port: $PORT"
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# List files in current directory
echo "=== Current directory contents ==="
ls -la

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found!"
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found!"
    exit 1
fi

# Check environment variables
echo "=== Environment Variables ==="
echo "DATABASE_URL: ${DATABASE_URL:0:20}..."  # Only show first 20 chars for security
echo "DATABASE_URL_SYNC: ${DATABASE_URL_SYNC:0:20}..."
echo "SECRET_KEY: ${SECRET_KEY:0:10}..."
echo "JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:10}..."
echo "ENVIRONMENT: $ENVIRONMENT"
echo "DEBUG: $DEBUG"

# Check if we're in production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "=== Running in production mode ==="
    
    # Run database migrations
    echo "Running database migrations..."
    if command -v alembic &> /dev/null; then
        echo "Alembic found, running migrations..."
        alembic upgrade head || {
            echo "WARNING: Database migration failed, but continuing..."
        }
    else
        echo "WARNING: alembic not found, skipping migrations..."
    fi
    
    # Start the application
    echo "Starting FastAPI application..."
    echo "Command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1"
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
else
    echo "=== Running in development mode ==="
    
    # Start the application with reload
    echo "Starting FastAPI application with reload..."
    echo "Command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi 