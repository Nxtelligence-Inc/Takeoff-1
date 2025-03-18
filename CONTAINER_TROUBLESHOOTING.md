# Container Troubleshooting Guide

This guide provides commands you can run inside your container to check its status and troubleshoot issues.

## Basic Container Status Commands

When you're inside a container shell (e.g., at `/app #` prompt), you can run these commands:

### Process Status

```bash
# Check running processes
ps aux

# Check Node.js processes specifically
ps aux | grep node
```

### File System

```bash
# List files in current directory
ls -la

# Check disk space
df -h

# Check directory sizes
du -sh *
```

### Network

```bash
# Check network interfaces
ip addr

# Check listening ports
netstat -tuln

# Check if the server is listening on port 3000
netstat -tuln | grep 3000

# Test connectivity to backend
curl -v http://backend:5000/health
```

### Application Status

```bash
# Check if server.js exists
ls -la server.js

# Check Node.js version
node -v

# Check npm version
npm -v

# Check environment variables
env | sort

# Check if critical environment variables are set
echo "CONTAINERIZED: $CONTAINERIZED"
echo "BACKEND_API_URL: $BACKEND_API_URL"
```

### Logs

```bash
# Check application logs (if they're being written to files)
ls -la logs/
cat logs/app.log

# Check system logs
dmesg | tail
```

## Troubleshooting Next.js Application

```bash
# Check if the .next directory exists and has content
ls -la .next/

# Check if the standalone directory exists
ls -la .next/standalone/

# Check if static files are present
ls -la .next/static/

# Check public directory
ls -la public/
```

## Testing the Application

```bash
# Test if the server responds locally
curl -v http://localhost:3000

# Check if the health endpoint responds
curl -v http://localhost:3000/health

# Check if the API proxy is working
curl -v http://localhost:3000/api/health
```

## Debugging Container Issues

```bash
# Check container startup logs
cat /var/log/startup.log

# Check if required directories exist
ls -la public/uploads
ls -la public/results
ls -la public/logos

# Check if the application can connect to the backend
curl -v http://backend:5000
```

## Restarting the Application

If you need to restart the application manually inside the container:

```bash
# Find the Node.js process
ps aux | grep node

# Kill the process (replace 123 with actual PID)
kill 123

# Start the application again
node server.js
```

## Checking Container Health in Coolify

From your host machine (not inside the container), you can run:

```bash
# Check container logs
docker logs drawing-ocr-frontend

# Check container status
docker ps | grep drawing-ocr-frontend

# Check container health
docker inspect --format='{{.State.Health.Status}}' drawing-ocr-frontend

# Check container stats (CPU, memory usage)
docker stats drawing-ocr-frontend
```

## Common Issues and Solutions

1. **Application not starting**: Check if `server.js` exists and if Node.js is installed correctly.
2. **Cannot connect to backend**: Check if the `BACKEND_API_URL` environment variable is set correctly.
3. **Missing files**: Check if all required directories and files are present.
4. **Port not listening**: Check if the application is running and listening on port 3000.
5. **Out of memory**: Check container memory usage with `docker stats`.
