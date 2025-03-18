# Backend Container Diagnostic Guide

Based on the output, it appears the backend container is using a very basic shell (sh) that doesn't support some of the syntax in our diagnostic command. Here's a simpler diagnostic command specifically for the backend container:

```sh
# Simple diagnostic command for backend container
# This will work after rebuilding with the updated Dockerfile that includes procps and net-tools
ps aux; echo; echo "Files:"; ls -la; echo; echo "Disk:"; df -h; echo; echo "Network:"; netstat -tuln; echo; echo "Python:"; python --version; echo; echo "Processes:"; ps -ef | grep gunicorn; echo; echo "Environment:"; env | grep -E 'API|NON|PYTHON'; echo; echo "Health Check:"; wget -O- http://localhost:5000/health 2>/dev/null || echo "Health endpoint not responding"
```

If the container doesn't have the required tools yet (before rebuilding), use this simpler command:

```sh
echo "Files:"; ls -la; echo; echo "Disk:"; df -h; echo; echo "Python:"; python --version; echo; echo "Environment:"; env
```

## Backend Container Analysis

Based on the diagnostic output, the backend container:

1. Is running Python 3.10.16
2. Has the expected directory structure with src/ and public/ directories
3. Is missing common system utilities like ps and netstat (fixed in updated Dockerfile)
4. Has the required environment variables set
5. Has the Flask application code in place

The main issue appears to be that the container is using a minimal Python image that doesn't include diagnostic tools. The updated Dockerfile.backend now includes:

- procps (for ps command)
- net-tools (for netstat command)
- curl and wget (for testing HTTP endpoints)

## Common Backend Container Issues

1. **Missing Python Dependencies**:
   - Check if all required Python packages are installed
   - Verify the requirements.txt file is complete

2. **API Endpoint Issues**:
   - Check if the Flask application is running and listening on the correct port
   - Verify the API endpoints are accessible

3. **Environment Variable Configuration**:
   - Ensure all required environment variables are set
   - Check for API keys and other configuration variables

4. **File System Permissions**:
   - Verify the container has write access to necessary directories
   - Check if shared volumes are properly mounted

## Backend Container Troubleshooting Commands

Here are some commands that should work in most basic shell environments:

### Check Processes
```sh
ps aux
```

### Check Python Version
```sh
python --version
python3 --version
```

### Check Flask Application
```sh
ps -ef | grep gunicorn
ps -ef | grep python
```

### Check Network
```sh
netstat -tuln
netstat -tuln | grep 5000
```

### Check Environment Variables
```sh
env
env | grep API
env | grep NON
```

### Check File System
```sh
ls -la
ls -la /app
ls -la /app/public
```

### Check Logs
```sh
tail -f /var/log/gunicorn.log
```

### Test API Endpoint
```sh
wget -O- http://localhost:5000/health
```

## Dockerfile.backend Analysis

The Dockerfile.backend appears to be correctly configured, but there might be issues with:

1. **Health Check Endpoint**:
   - Ensure the Flask application has a `/health` endpoint
   - Add a health check to the Dockerfile

2. **Environment Variables**:
   - Make sure all required environment variables are set
   - Check for API keys and other configuration

3. **Dependencies**:
   - Verify all system and Python dependencies are installed
   - Check for any missing libraries

## Implemented Fixes

1. **Added Health Endpoint**:
   - Added a `/health` endpoint to src/api.py
   - Returns a 200 status code and JSON response indicating the service is healthy

2. **Updated Dockerfile.backend**:
   - Added procps for process monitoring (ps command)
   - Added net-tools for network diagnostics (netstat command)
   - Added curl and wget for HTTP testing
   - Added a healthcheck that tests the /health endpoint

3. **Updated docker-compose-coolify.yaml**:
   - Added dependency condition to ensure frontend only starts when backend is healthy
   - Configured resource limits for stable operation

## Verifying the Backend Container

After rebuilding with the updated Dockerfile, you should be able to:

1. Run the full diagnostic command to get detailed information
2. Test the health endpoint with `wget -O- http://localhost:5000/health`
3. Monitor processes with `ps aux | grep gunicorn`
4. Check network connections with `netstat -tuln | grep 5000`

These changes make the backend container more robust and easier to troubleshoot.
