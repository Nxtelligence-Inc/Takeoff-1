# Multi-stage build for a combined frontend and backend container

# Frontend build stage
FROM node:20.11-alpine AS frontend-builder

# Install git
RUN apk add --no-cache git python3 make g++ libc6-compat

# Set working directory
WORKDIR /app

# Clone the repository
RUN git clone https://github.com/Nxtelligence-Inc/Takeoff-1.git /tmp/repo

# Copy package files from the cloned repository
RUN cp -r /tmp/repo/Frontend/package*.json ./

# Clean install of dependencies
RUN npm install --legacy-peer-deps && \
    npm install -D tailwindcss postcss autoprefixer

# Copy the rest of the frontend code from the cloned repository
RUN cp -r /tmp/repo/Frontend/* ./

# Create a script to fix import paths
RUN echo '// Script to fix import paths in Next.js files\n\
const fs = require("fs");\n\
const path = require("path");\n\
\n\
// Function to recursively find all .tsx and .ts files\n\
function findFiles(dir, fileList = []) {\n\
  const files = fs.readdirSync(dir);\n\
  \n\
  files.forEach(file => {\n\
    const filePath = path.join(dir, file);\n\
    const stat = fs.statSync(filePath);\n\
    \n\
    if (stat.isDirectory()) {\n\
      findFiles(filePath, fileList);\n\
    } else if (file.endsWith(".tsx") || file.endsWith(".ts")) {\n\
      fileList.push(filePath);\n\
    }\n\
  });\n\
  \n\
  return fileList;\n\
}\n\
\n\
// Function to fix imports in a file\n\
function fixImports(filePath) {\n\
  let content = fs.readFileSync(filePath, "utf8");\n\
  \n\
  // Replace @/ imports with relative paths\n\
  content = content.replace(/from\\s+["\\']@\\/([^"\\']+)["\\']/g, (match, importPath) => {\n\
    return `from "./${importPath}"`;\n\
  });\n\
  \n\
  fs.writeFileSync(filePath, content);\n\
  console.log(`Fixed imports in ${filePath}`);\n\
}\n\
\n\
// Main function\n\
function main() {\n\
  const files = findFiles(".");\n\
  \n\
  files.forEach(file => {\n\
    fixImports(file);\n\
  });\n\
  \n\
  console.log(`Fixed imports in ${files.length} files`);\n\
}\n\
\n\
main();\n' > fix-imports.js && node fix-imports.js

# Set environment variables for build
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_API_URL=http://localhost:5000 \
    NODE_PATH=/app

# Build the Next.js application
RUN NODE_PATH=/app npm run build

# Backend stage
FROM python:3.9-slim

# Install Node.js for the frontend and git
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set up directories
WORKDIR /app
RUN mkdir -p /app/frontend /app/backend /app/public/uploads /app/public/results

# Clone the repository if it doesn't exist in the build context
RUN git clone https://github.com/Nxtelligence-Inc/Takeoff-1.git /tmp/repo

# Copy backend files from the cloned repository
RUN cp -r /tmp/repo/src/ /app/backend/src/
RUN cp /tmp/repo/requirements.txt /app/backend/

# Install Python dependencies
RUN cd /app/backend && pip install --no-cache-dir -r requirements.txt

# Copy built frontend from the builder stage
COPY --from=frontend-builder /app /app/frontend

# Set up supervisor to run both services
RUN echo "[supervisord]\nnodaemon=true\n\n\
[program:backend]\ncommand=gunicorn --bind 0.0.0.0:5000 src.api:app\ndirectory=/app/backend\nautostart=true\nautorestart=true\nstdout_logfile=/dev/stdout\nstdout_logfile_maxbytes=0\nstderr_logfile=/dev/stderr\nstderr_logfile_maxbytes=0\n\n\
[program:frontend]\ncommand=npm start\ndirectory=/app/frontend\nautostart=true\nautorestart=true\nstdout_logfile=/dev/stdout\nstdout_logfile_maxbytes=0\nstderr_logfile=/dev/stderr\nstderr_logfile_maxbytes=0" > /etc/supervisor/conf.d/services.conf

# Expose ports
EXPOSE 3000 5000

# Start supervisor to manage both services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
