#!/bin/bash

# Exit on any error
set -e

echo "Starting SoleCraft API deployment..."
echo "Environment: $ENVIRONMENT"
echo "Python version: $(python --version)"

# Check if we're in production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Running in production mode"
    
    # Run database migrations
    echo "Running database migrations..."
    if command -v alembic &> /dev/null; then
        alembic upgrade head || {
            echo "Warning: Database migration failed, but continuing..."
        }
    else
        echo "Warning: alembic not found, skipping migrations..."
    fi
    
    # Start the application
    echo "Starting FastAPI application..."
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
else
    echo "Running in development mode"
    
    # Start the application with reload
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi 