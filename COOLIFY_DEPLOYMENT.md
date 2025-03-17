# Deploying to Coolify with a Single Docker Container

This guide explains how to deploy the ICF Analysis application to Coolify using a single Docker container that runs both the frontend and backend services.

## Overview

We've simplified the deployment by:
1. Creating a single Dockerfile that builds both frontend and backend
2. Using Supervisor to run both services in one container
3. Simplifying the docker-compose.yaml file

## Deployment Steps

### 1. Push Your Code to GitHub

Make sure your repository includes:
- The new `Dockerfile`
- The updated `docker-compose.yaml`
- All your source code (Frontend/ and src/ directories)
- All configuration files

### 2. Set Up in Coolify

1. Log in to your Coolify dashboard
2. Create a new resource
3. Select "Application" as the resource type
4. Choose "Docker" as the deployment type (not Nixpacks)
5. Connect to your GitHub repository
6. Select the branch (main)

### 3. Configure Docker Settings

1. Set the Dockerfile path to `Dockerfile` (the root Dockerfile we created)
2. Set the Docker Compose file path to `docker-compose.yaml`
3. Set the service name to `icf-app`

### 4. Configure Environment Variables

Add the required environment variables:
- `OPENAI_API_KEY`
- `GOOGLE_CREDENTIALS_JSON`
- `CLAUDE_API_KEY`
- `NON_INTERACTIVE=true`

### 5. Configure Network Settings

1. Set the public port to 3010 (or your preferred port)
2. Enable HTTPS if desired

### 6. Deploy

Click "Save" or "Deploy" to start the deployment process.

## How It Works

The single container approach works as follows:

1. The Dockerfile uses a multi-stage build:
   - First stage builds the Next.js frontend
   - Second stage sets up the Python backend
   - The frontend build is copied into the final image

2. Supervisor is used to run both services:
   - The backend runs on port 5000
   - The frontend runs on port 3000
   - Both services log to stdout/stderr for easy monitoring

3. The frontend is configured to communicate with the backend at localhost:5000

## Troubleshooting

### Common Issues

1. **Build Failures**: Check the logs for any build errors. The most common issues are related to dependency installation.

2. **Runtime Errors**: If the application starts but doesn't work correctly, check the logs for runtime errors.

3. **Connection Issues**: If the frontend cannot connect to the backend, ensure the `NEXT_PUBLIC_API_URL` environment variable is set correctly.

### Logs

Coolify provides access to logs, which can be helpful for debugging:
- View logs in the application dashboard
- Both frontend and backend logs will be visible since they're in the same container
