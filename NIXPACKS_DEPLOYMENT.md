# Deploying with Nixpacks

This guide explains how to deploy the ICF Analysis application using Nixpacks, which is used by platforms like Railway and Render.

## Prerequisites

- A GitHub repository with your code
- A Railway or Render account (or any platform that supports Nixpacks)

## Deployment Files

This repository includes several files to facilitate deployment with Nixpacks:

1. `nixpacks.toml` - Configuration for Nixpacks build process
2. `start.sh` - Script to start both frontend and backend services
3. `Procfile` - Alternative to start.sh for platforms that support it

## Deployment Steps

### Option 1: Deploy on Railway

1. Create a new project in Railway
2. Connect your GitHub repository
3. Railway will automatically detect the Nixpacks configuration
4. Add the required environment variables from `.env.example`
5. Deploy the application

### Option 2: Deploy on Render

1. Create a new Web Service in Render
2. Connect your GitHub repository
3. Select "Nixpacks" as the build method
4. Add the required environment variables from `.env.example`
5. Deploy the service

## Environment Variables

Make sure to set these environment variables in your deployment platform:

- `OPENAI_API_KEY` - Your OpenAI API key
- `CLAUDE_API_KEY` - Your Anthropic Claude API key
- `GOOGLE_CREDENTIALS_JSON` - Your Google Cloud Vision API credentials as a JSON string
- `NON_INTERACTIVE` - Set to "true" for deployment

## Port Configuration

The application runs on the following ports:
- Frontend: Port 3000
- Backend API: Port 5000

Most deployment platforms will automatically assign a port via the `PORT` environment variable. The start script will need to be updated if your platform requires a specific port configuration.

## Troubleshooting

### Common Issues

1. **Build Failures**: Ensure your repository includes all necessary files and dependencies.

2. **Runtime Errors**: Check the logs for any runtime errors. Common issues include missing environment variables or incorrect API keys.

3. **Connection Issues**: If the frontend cannot connect to the backend, ensure the `NEXT_PUBLIC_API_URL` is set correctly.

### Logs

Most platforms provide access to logs, which can be helpful for debugging:

- Railway: View logs in the project dashboard
- Render: View logs in the Web Service dashboard
