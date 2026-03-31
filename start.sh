#!/usr/bin/env bash
# File: start.sh
# Description: Dynamically calculate the number of Gunicorn workers based on available CPU cores
# and the environment. Starts the FastAPI application.

# Get the number of CPU cores available to the container
CPU_CORES=$(nproc)

# Determine the environment (default to 'prod' if not set)
ENVIRONMENT=${RUN_ENV:-local}

# Calculate workers based on environment
if [ "$ENVIRONMENT" = "local" ]; then
    # Use (1 * CPU_CORES) + 1 for local environments to reduce resource usage
    WORKERS=$((1 * CPU_CORES + 1))
else
    # Use (2 * CPU_CORES) + 1 for beta/prod environments
    WORKERS=$((2 * CPU_CORES + 1))
fi

# Cap the number of workers to avoid overloading memory
MAX_WORKERS=8
if [ $WORKERS -gt $MAX_WORKERS ]; then
    WORKERS=$MAX_WORKERS
fi

WORKERS=1

# Log the calculated number of workers
echo "Starting Gunicorn with $WORKERS workers based on $CPU_CORES CPU cores in $ENVIRONMENT environment."

# Execute Gunicorn with the calculated number of workers
exec ./wait-for-it.sh database:3306 -t 30 -- gunicorn -w $WORKERS -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --forwarded-allow-ips="*" api.main:app
