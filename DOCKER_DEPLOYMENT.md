# Docker Deployment Guide for ICF Analysis App

This guide explains how to deploy the ICF Analysis application using Docker for easy demonstration.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your system

## Deployment Steps

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd DrawingOCR
```

### 2. Build and Start the Containers

```bash
docker-compose up -d --build
```

This command will:
- Build the frontend and backend Docker images
- Start the containers in detached mode
- Set up the necessary volumes for persistent storage

### 3. Access the Application

Once the containers are running, you can access the application at:

```
http://localhost:3000
```

### 4. View Logs (Optional)

To view the logs of the running containers:

```bash
# View frontend logs
docker-compose logs -f frontend

# View backend logs
docker-compose logs -f backend
```

### 5. Stop the Application

When you're done with the demo, you can stop the containers:

```bash
docker-compose down
```

## Container Architecture

The application is containerized using two services:

1. **Frontend (Next.js)**
   - Runs the Next.js application
   - Serves the web interface
   - Communicates with the backend service for analysis

2. **Backend (Python/Flask)**
   - Processes foundation plan images
   - Runs the Python analysis scripts
   - Provides an API for the frontend

Both services share volumes for:
- Uploaded images (`/app/public/uploads`)
- Analysis results (`/app/public/results`)

## Customization

### Environment Variables

You can customize the deployment by modifying the environment variables in `docker-compose.yml`:

- `CONTAINERIZED`: Set to "true" to enable containerized mode
- `BACKEND_API_URL`: URL of the backend API service
- `NON_INTERACTIVE`: Set to "true" for non-interactive Python script execution

### Ports

By default, the application runs on port 3000. To use a different port, modify the `ports` section in `docker-compose.yml`:

```yaml
ports:
  - "8080:3000"  # Change 8080 to your desired port
```

## Troubleshooting

### Container Startup Issues

If containers fail to start:

```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs
```

### Volume Permissions

If you encounter permission issues with the shared volumes:

```bash
# Fix permissions (run from host)
sudo chown -R 1000:1000 ./data
```

### Network Issues

If the frontend cannot connect to the backend:

1. Ensure both containers are running
2. Check that the `BACKEND_API_URL` is set correctly
3. Verify network settings in `docker-compose.yml`

## Pre-populating Demo Data

For a smoother demo experience, you can pre-populate the application with sample data:

1. Create a sample analysis directory:
   ```bash
   mkdir -p data/results/demo
   ```

2. Copy sample data files:
   ```bash
   cp path/to/sample/analysis_results.json data/results/demo/
   cp path/to/sample/image.png data/uploads/demo.png
   ```

3. Start the containers with the pre-populated data:
   ```bash
   docker-compose up -d
