# Frontend Container Diagnostic Command

Now that the backend is running healthy, here's a comprehensive diagnostic command for the frontend container terminal. This command will check the frontend's status, connectivity to the backend, and overall health.

```bash
echo "=== FRONTEND CONTAINER DIAGNOSTIC ===" && \
echo -e "\n=== PROCESS STATUS ===" && \
ps aux && \
echo -e "\n=== NODE PROCESS ===" && \
ps aux | grep node && \
echo -e "\n=== ENVIRONMENT VARIABLES ===" && \
env | grep -E 'NODE|CONTAINERIZED|BACKEND|NEXT' && \
echo -e "\n=== FILE SYSTEM ===" && \
ls -la && \
echo -e "\n=== SERVER.JS FILE ===" && \
cat server.js | head -10 && \
echo -e "\n=== NEXT.JS BUILD ===" && \
ls -la .next/ && \
echo -e "\n=== NETWORK STATUS ===" && \
netstat -tuln | grep 3000 && \
echo -e "\n=== BACKEND CONNECTIVITY ===" && \
curl -v http://backend:5000/health && \
echo -e "\n=== FRONTEND HEALTH ===" && \
curl -v http://localhost:3000 -o /dev/null && \
echo -e "\n=== DIAGNOSTIC COMPLETE ==="
```

## What This Command Checks

1. **Process Status**: Shows all running processes in the container
2. **Node Process**: Specifically shows Node.js processes
3. **Environment Variables**: Displays all relevant environment variables
4. **File System**: Lists files in the current directory
5. **Server.js File**: Shows the first 10 lines of the server.js file
6. **Next.js Build**: Lists the contents of the .next directory
7. **Network Status**: Checks if port 3000 is being listened on
8. **Backend Connectivity**: Tests connectivity to the backend's health endpoint
9. **Frontend Health**: Tests if the frontend is responding on port 3000

## Simplified Command (If Curl Is Not Available)

If curl is not available in the container, use this simplified command:

```bash
echo "=== FRONTEND CONTAINER DIAGNOSTIC ===" && \
echo -e "\n=== PROCESS STATUS ===" && \
ps aux && \
echo -e "\n=== NODE PROCESS ===" && \
ps aux | grep node && \
echo -e "\n=== ENVIRONMENT VARIABLES ===" && \
env | grep -E 'NODE|CONTAINERIZED|BACKEND|NEXT' && \
echo -e "\n=== FILE SYSTEM ===" && \
ls -la && \
echo -e "\n=== SERVER.JS FILE ===" && \
cat server.js | head -10 && \
echo -e "\n=== NEXT.JS BUILD ===" && \
ls -la .next/ && \
echo -e "\n=== NETWORK STATUS ===" && \
netstat -tuln | grep 3000 && \
echo -e "\n=== DIAGNOSTIC COMPLETE ==="
```

## Testing Backend Connectivity Without Curl

If curl is not available, you can test backend connectivity using Node.js:

```bash
node -e "const http = require('http'); const req = http.get('http://backend:5000/health', (res) => { console.log('Status:', res.statusCode); let data = ''; res.on('data', (chunk) => data += chunk); res.on('end', () => console.log(data)); }); req.on('error', (e) => console.error('Error:', e.message)); req.end();"
```

## Testing Frontend Health Without Curl

Similarly, you can test the frontend health using Node.js:

```bash
node -e "const http = require('http'); const req = http.get('http://localhost:3000', (res) => { console.log('Frontend Status:', res.statusCode); }); req.on('error', (e) => console.error('Error:', e.message)); req.end();"
```

## Analyzing the Results

After running the diagnostic command, look for:

1. **Node Process**: Ensure a Node.js process is running with server.js
2. **Environment Variables**: Check that BACKEND_API_URL is set correctly
3. **Server.js File**: Verify the server.js file exists and contains valid code
4. **Network Status**: Confirm port 3000 is being listened on
5. **Backend Connectivity**: Verify the backend health endpoint returns a 200 status
6. **Frontend Health**: Ensure the frontend returns a 200 status

If any of these checks fail, refer to the FRONTEND_CONTAINER_FIX.md file for troubleshooting steps.
