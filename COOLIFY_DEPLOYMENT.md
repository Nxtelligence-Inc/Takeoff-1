# Coolify/Linux Deployment Guide for DrawingOCR

This guide explains how to deploy the DrawingOCR application on Coolify or any Linux-based Docker environment. The application consists of a Next.js frontend and a Flask backend, both containerized for easy deployment.

## Prerequisites

- Linux server with Docker and Docker Compose installed
- Docker Hub account (for pulling the pre-built images)
- [Coolify](https://coolify.io/) (optional, for managed deployments)

## Deployment Options

### Option 1: Using Pre-built Docker Hub Images

The easiest way to deploy is using the pre-built Docker images from Docker Hub:

1. **Clone this repository or download the `docker-compose-coolify.yaml` file**

2. **Deploy using Docker Compose**

   ```bash
   docker-compose -f docker-compose-coolify.yaml up -d
   ```

   This will pull the pre-built images from Docker Hub and start the containers.

3. **Access the application**

   - Frontend: http://your-server-ip:3010
   - Backend API: http://your-server-ip:5002

### Option 2: Building and Pushing Your Own Images

If you want to customize the application or build your own images:

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd DrawingOCR
   ```

2. **Configure environment variables (optional)**

   Create a `.env` file in the root directory with your API keys:

   ```
   OPENAI_API_KEY=your-openai-api-key
   CLAUDE_API_KEY=your-claude-api-key
   ```

3. **Build and push the Docker images**

   Use the provided script to build multi-platform Docker images and push them to Docker Hub:

   ```bash
   ./build-and-push.sh
   ```

   This script uses Docker BuildKit to create images compatible with multiple Linux architectures (amd64 and arm64).

   > **Note:** You need to be logged in to Docker Hub (`docker login`) before running this script.
   > You may also need to modify the image names in the script to use your Docker Hub username.

4. **Deploy using Docker Compose**

   Update the image names in `docker-compose-coolify.yaml` if you changed them, then:

   ```bash
   docker-compose -f docker-compose-coolify.yaml up -d
   ```

## Deploying on Coolify

Coolify is a self-hostable Heroku/Netlify alternative that makes deployment easy:

1. **Install Coolify on your server** following the [official documentation](https://coolify.io/docs/installation)

2. **Create a new service** in the Coolify dashboard

3. **Configure the service**:
   - Select "Docker Compose" as the deployment method
   - Provide the repository URL or upload the `docker-compose-coolify.yaml` file
   - Configure environment variables if needed

4. **Deploy the service**

   Coolify will pull the images and start the containers according to the configuration in `docker-compose-coolify.yaml`.

## Configuration

### Environment Variables

The application uses several environment variables for configuration. These can be set in different ways depending on your deployment method:

#### Setting Environment Variables in Coolify

Coolify provides a user-friendly way to manage environment variables:

1. In the Coolify dashboard, navigate to your service
2. Go to the "Environment Variables" section
3. Add each variable with its corresponding value
4. For sensitive data like API keys, use Coolify's secret management feature

#### Required Environment Variables

- `NON_INTERACTIVE=true`: Required for the backend to run in non-interactive mode
- `CONTAINERIZED=true`: Required for the frontend to run in containerized mode
- `BACKEND_API_URL=http://backend:5000`: Required for the frontend to communicate with the backend

#### Optional Environment Variables for LLM Features

If you want to use the LLM features for dimension extraction:

- `OPENAI_API_KEY`: Your OpenAI API key
- `CLAUDE_API_KEY`: Your Anthropic Claude API key

#### Optional Environment Variables for Google Cloud Vision

If you want to use Google Cloud Vision:

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google Cloud credentials file
- Alternatively, you can mount your credentials file as a volume

#### Using .env Files (Local Deployment)

For local deployment, you can use a .env file:

1. Create a `.env` file in the root directory
2. Add your environment variables in the format `KEY=value`
3. Uncomment the volume mount in `docker-compose-coolify.yaml`:
   ```yaml
   volumes:
     - ./.env:/app/.env
   ```

### Resource Limits

The `docker-compose-coolify.yaml` file includes resource limits to ensure stable operation:

- Backend: 2GB memory limit, 1GB memory reservation
- Frontend: 1GB memory limit, 512MB memory reservation

You can adjust these limits based on your server's capabilities.

### Health Checks

The `docker-compose-coolify.yaml` file includes health checks to monitor the containers:

- Backend: Checks the `/health` endpoint every 30 seconds
- Frontend: Checks the `/health` endpoint every 30 seconds

## Shared Data

The frontend and backend containers share a Docker volume for uploads and results. This ensures that:

1. Files uploaded through the frontend are accessible to the backend for processing
2. Results generated by the backend are accessible to the frontend for display

## Troubleshooting

### Container Logs

To view logs for the containers:

```bash
# Frontend logs
docker logs drawing-ocr-frontend

# Backend logs
docker logs drawing-ocr-backend
```

### Rebuilding Containers

If you make changes to the code, you'll need to rebuild the containers:

```bash
./build-and-push.sh
docker-compose -f docker-compose-coolify.yaml up -d --force-recreate
```

### Stopping Containers

To stop the containers:

```bash
docker-compose -f docker-compose-coolify.yaml down
```

To stop the containers and remove volumes:

```bash
docker-compose -f docker-compose-coolify.yaml down -v
```

## Differences from Docker Desktop Deployment

The Coolify/Linux deployment differs from the Docker Desktop deployment in the following ways:

1. **Multi-platform images**: The images are built for multiple Linux architectures (amd64 and arm64)
2. **Resource limits**: Explicit memory limits are set to ensure stable operation
3. **Health checks**: Container health is monitored to detect and recover from failures
4. **Pre-built images**: The deployment uses pre-built images from Docker Hub instead of building them locally

These changes ensure that the application runs reliably on Linux servers and can be easily deployed using Coolify or any other Docker-based deployment platform.
