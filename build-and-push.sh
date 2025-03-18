#!/bin/bash
set -e

# Script to build and push Docker images for Coolify/Linux deployment
# Uses BuildKit for multi-platform builds targeting Linux

echo "Building and pushing Docker images for DrawingOCR..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Note about Docker Hub login
echo "Note: Ensure you are logged in to Docker Hub with 'docker login' before proceeding."
echo "Continuing with build and push..."

# Ensure BuildKit is enabled
export DOCKER_BUILDKIT=1

# Define target platforms (Linux variants commonly used in cloud environments)
# Start with just amd64 for compatibility, add arm64 if needed
PLATFORMS="linux/amd64"

# Check if buildx is available
if ! docker buildx version &>/dev/null; then
    echo "Docker BuildKit (buildx) is not available. Falling back to standard build."
    
    # Build backend image (standard)
    echo "Building backend image..."
    docker build -t rb0001/takeoff1:backend -f Dockerfile.backend .
    
    # Build frontend image (standard)
    echo "Building frontend image..."
    docker build -t rb0001/takeoff1:frontend -f Dockerfile.frontend .
    
    # Push images to Docker Hub
    echo "Pushing backend image to Docker Hub..."
    docker push rb0001/takeoff1:backend
    
    echo "Pushing frontend image to Docker Hub..."
    docker push rb0001/takeoff1:frontend
else
    # Create a new builder instance if it doesn't exist
    if ! docker buildx inspect mybuilder &>/dev/null; then
        echo "Creating a new BuildKit builder instance..."
        docker buildx create --name mybuilder --use
    else
        echo "Using existing BuildKit builder instance..."
        docker buildx use mybuilder
    fi
    
    # Ensure the builder is running
    docker buildx inspect --bootstrap
    
    echo "Building and pushing using multi-platform build for: $PLATFORMS"
    
    # Build and push backend image for multiple platforms
    echo "Building and pushing backend image..."
    if ! docker buildx build --platform $PLATFORMS \
        -t rb0001/takeoff1:backend \
        -f Dockerfile.backend \
        --push .; then
        
        echo "Multi-platform build failed. Falling back to standard build for backend."
        docker build -t rb0001/takeoff1:backend -f Dockerfile.backend .
        docker push rb0001/takeoff1:backend
    fi
    
    # Build and push frontend image for multiple platforms
    echo "Building and pushing frontend image..."
    if ! docker buildx build --platform $PLATFORMS \
        -t rb0001/takeoff1:frontend \
        -f Dockerfile.frontend \
        --push .; then
        
        echo "Multi-platform build failed. Falling back to standard build for frontend."
        docker build -t rb0001/takeoff1:frontend -f Dockerfile.frontend .
        docker push rb0001/takeoff1:frontend
    fi
fi

echo "Multi-platform build and push completed successfully!"
echo "Linux-compatible images are available at:"
echo "  - rb0001/takeoff1:backend"
echo "  - rb0001/takeoff1:frontend"
echo ""
echo "These images support the following platforms: $PLATFORMS"
echo "To deploy with Coolify, use the docker-compose-coolify.yaml file."
