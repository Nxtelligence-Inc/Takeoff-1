#!/bin/sh

# Create necessary directories
mkdir -p public/uploads public/results

# Set default ports if not provided by the environment
BACKEND_PORT=${BACKEND_PORT:-5001}
PORT=${PORT:-3002}

# Set API URL for frontend
export NEXT_PUBLIC_API_URL="http://localhost:${BACKEND_PORT}"

# Start the backend in the background
gunicorn --bind 0.0.0.0:${BACKEND_PORT} src.api:app &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 3

# Start the frontend with the PORT environment variable
cd Frontend && PORT=${PORT} npm run dev

# If frontend exits, kill the backend
kill $BACKEND_PID
