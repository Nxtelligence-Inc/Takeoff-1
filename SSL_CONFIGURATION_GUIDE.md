# SSL Configuration Guide for Coolify Deployment

## Issue Identified

You're experiencing an SSL error when accessing the site at coolify.jmac.pro:

```
This site can't provide a secure connection
coolify.jmac.pro sent an invalid response.
ERR_SSL_PROTOCOL_ERROR
```

This error indicates an issue with the SSL/TLS configuration, not with the containers themselves. The diagnostic output shows that both the frontend and backend containers are working correctly internally.

## Understanding the Problem

The `ERR_SSL_PROTOCOL_ERROR` typically occurs when:

1. The SSL certificate is invalid or expired
2. The server is not properly configured to handle SSL/TLS connections
3. There's a mismatch between the client and server SSL/TLS protocols
4. The reverse proxy is not properly forwarding HTTPS traffic to the containers

## Solution Steps

### 1. Check Coolify SSL Configuration

Coolify typically handles SSL certificates through its dashboard:

1. Log in to your Coolify dashboard
2. Navigate to your application
3. Go to the "Settings" or "Configuration" section
4. Check the SSL/TLS configuration
5. Ensure that SSL is enabled and a valid certificate is configured

### 2. Verify Certificate Status

Check if the SSL certificate for coolify.jmac.pro is valid:

```bash
# Using OpenSSL
openssl s_client -connect coolify.jmac.pro:443 -servername coolify.jmac.pro
```

Look for:
- Certificate validity dates
- Certificate chain completeness
- Certificate issued to the correct domain

### 3. Configure Reverse Proxy

If you're using a reverse proxy (like Nginx or Traefik) in front of Coolify:

1. Check the reverse proxy configuration
2. Ensure it's properly forwarding HTTPS traffic to the containers
3. Verify the SSL certificate is correctly configured in the reverse proxy

#### Example Nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name coolify.jmac.pro;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    
    # Forward to your application
    location / {
        proxy_pass http://localhost:3010;  # Frontend port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Forward API requests to backend
    location /api {
        proxy_pass http://localhost:5002;  # Backend port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Coolify-specific SSL Configuration

If you're using Coolify's built-in SSL features:

1. Go to your Coolify dashboard
2. Navigate to your application settings
3. Look for "SSL/TLS" or "HTTPS" settings
4. Choose one of the following options:
   - **Let's Encrypt**: Automatically obtain and renew certificates
   - **Custom Certificate**: Upload your own certificate and key
   - **Cloudflare**: If you're using Cloudflare as a proxy

5. If using Let's Encrypt, ensure:
   - The domain coolify.jmac.pro points to your server
   - Port 80 is open for the ACME challenge
   - The Coolify server has permission to create certificates

### 5. Check Coolify Proxy Settings

Coolify uses a reverse proxy (typically Traefik) to handle incoming connections:

1. In the Coolify dashboard, check the proxy settings
2. Ensure the proxy is configured to handle HTTPS connections
3. Verify that the proxy is forwarding traffic to the correct containers and ports

### 6. Debugging SSL Issues

If the above steps don't resolve the issue, try these debugging steps:

1. **Check SSL with SSL Labs**:
   Visit https://www.ssllabs.com/ssltest/ and enter your domain

2. **Test with curl**:
   ```bash
   curl -vI https://coolify.jmac.pro
   ```
   Look for SSL handshake errors in the output

3. **Check Coolify logs**:
   ```bash
   # If Coolify is running in Docker
   docker logs coolify-proxy
   ```

4. **Verify DNS configuration**:
   ```bash
   dig coolify.jmac.pro
   ```
   Ensure it points to the correct IP address

## Quick Fixes

### Option 1: Disable SSL Temporarily

If you need immediate access, you can temporarily access the site over HTTP:
- Try accessing http://coolify.jmac.pro (without HTTPS)
- Note: This is not secure and should only be used for testing

### Option 2: Use Cloudflare as a Proxy

Cloudflare can handle SSL termination for you:
1. Sign up for a free Cloudflare account
2. Add your domain to Cloudflare
3. Set the SSL/TLS encryption mode to "Flexible" temporarily
4. Update your domain's nameservers to use Cloudflare

### Option 3: Regenerate SSL Certificate

If the certificate is invalid:
1. In Coolify dashboard, go to your application settings
2. Find the SSL configuration
3. Delete the existing certificate
4. Generate a new certificate or upload a new one

## Long-term Solution

For a robust SSL setup:

1. Use Let's Encrypt with auto-renewal
2. Implement proper SSL termination at the reverse proxy level
3. Configure secure SSL protocols and ciphers
4. Set up HTTP to HTTPS redirection
5. Implement HSTS for added security

## Coolify SSL Configuration Example

```yaml
# In your Coolify configuration
services:
  frontend:
    # ... other configuration
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`coolify.jmac.pro`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=myresolver"
      - "traefik.http.services.frontend.loadbalancer.server.port=3000"
  
  backend:
    # ... other configuration
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`coolify.jmac.pro`) && PathPrefix(`/api`)"
      - "traefik.http.routers.backend.entrypoints=websecure"
      - "traefik.http.routers.backend.tls.certresolver=myresolver"
      - "traefik.http.services.backend.loadbalancer.server.port=5000"
```

This configuration assumes Traefik is being used as the reverse proxy with a certificate resolver named "myresolver".
