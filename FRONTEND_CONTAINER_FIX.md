# Frontend Container Troubleshooting and Fix

Based on the diagnostic output from your container, I've identified several issues and solutions:

## Current Issues

1. **Port Already in Use**: 
   - Error: `listen EADDRINUSE: address already in use 172.22.0.3:3000`
   - A Next.js server process is already running (PID 1), but might not be functioning correctly

2. **Missing Standalone Directory**:
   - `.next/standalone/` directory is missing, which is critical for Next.js standalone deployment
   - This suggests an issue with the build process or file copying in the Dockerfile

3. **Next.js Build Configuration**:
   - The build appears to be incomplete or incorrectly configured
   - The standalone output mode might not be properly set up

## Immediate Fix

To fix the container issue:

1. **Restart the container** in Coolify dashboard
   - This will terminate all processes and start fresh

2. If that doesn't work, try **modifying the Dockerfile.frontend**:

```dockerfile
# Modify the build stage to ensure standalone output
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY Frontend/ .

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV CONTAINERIZED=true
ENV BACKEND_API_URL=http://backend:5000

# Ensure next.config.js has output: 'standalone'
RUN echo "Verifying next.config.js contains standalone output..." && \
    grep -q "output.*standalone" next.config.mjs || \
    echo "Warning: standalone output may not be configured"

# Build the application with explicit standalone output
RUN npm run build

# Verify standalone directory exists after build
RUN ls -la .next/ && \
    if [ ! -d ".next/standalone" ]; then \
    echo "Error: .next/standalone directory not created during build"; \
    exit 1; \
    fi

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV CONTAINERIZED=true
ENV BACKEND_API_URL=http://backend:5000

# Create necessary directories
RUN mkdir -p public/uploads public/results public/logos

# Copy built application - ensure standalone directory is copied
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Add a healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "const http = require('http'); \
    const options = { hostname: 'localhost', port: 3000, path: '/', timeout: 2000 }; \
    const req = http.get(options, (res) => process.exit(res.statusCode >= 200 && res.statusCode < 400 ? 0 : 1)); \
    req.on('error', () => process.exit(1)); \
    req.end();"

# Expose the port the app runs on
EXPOSE 3000

# Run the application with explicit port binding
CMD ["node", "server.js"]
```

3. **Rebuild and redeploy** the container with the updated Dockerfile

## Checking Next.js Configuration

Verify that your `next.config.mjs` file includes the standalone output configuration:

```javascript
// In next.config.mjs
const nextConfig = {
  // ... other config
  output: 'standalone',
  // ... other config
}
```

## Alternative Solution: Manual Fix Inside Container

If you can't rebuild the container immediately, try these steps inside the container:

1. **Find and kill the existing Next.js process**:
   ```bash
   # Find the process ID
   ps aux
   
   # Kill the process (replace 1 with the actual PID if different)
   kill 1
   ```

2. **Check if the server.js file is correct**:
   ```bash
   # View the content of server.js
   cat server.js | head -20
   ```

3. **Try starting the server with a different port**:
   ```bash
   # Set a different port
   export PORT=3001
   
   # Start the server
   node server.js
   ```

## Long-term Fix

1. **Update your Next.js configuration**:
   - Ensure `output: 'standalone'` is set in next.config.mjs
   - Verify that the build process is creating the standalone directory

2. **Update the Dockerfile**:
   - Add verification steps to ensure the standalone directory is created
   - Add a healthcheck to monitor the application status
   - Consider adding debugging tools like curl to the container

3. **Update docker-compose-coolify.yaml**:
   - Add a healthcheck configuration
   - Consider adding a startup delay to ensure the backend is ready before the frontend starts

## Debugging Commands for Next.js Standalone

```bash
# Check if the server.js file is the correct one
cat server.js | grep -A 10 "const server ="

# Check Next.js configuration
cat package.json | grep next

# Try running with debugging
NODE_DEBUG=http,net node server.js
```

## Coolify-specific Recommendations

1. **Check Coolify logs** for the container from the Coolify dashboard
2. **Verify environment variables** are correctly set in Coolify
3. **Check network settings** to ensure the frontend can reach the backend
4. **Consider using a custom health check** in Coolify configuration
