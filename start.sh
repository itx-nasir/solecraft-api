#!/bin/bash

# Exit on any error
set -e

echo "Starting SoleCraft API deployment..."

# Check if we're in production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Running in production mode"
    
    # Run database migrations
    echo "Running database migrations..."
    alembic upgrade head || {
        echo "Warning: Database migration failed, but continuing..."
    }
    
    # Start the application
    echo "Starting FastAPI application..."
    exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
else
    echo "Running in development mode"
    
    # Start the application with reload
    exec uvicorn main:app --host 0.0.0.0 --port $PORT --reload
fi 