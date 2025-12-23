#!/bin/sh
# Docker entrypoint script for SSL-enabled nginx
# This script ensures SSL certificates exist before starting nginx

SSL_CERT="/etc/nginx/ssl/server.crt"
SSL_KEY="/etc/nginx/ssl/server.key"
SSL_DIR="/etc/nginx/ssl"

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

# Check if SSL certificates exist
if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
    echo "SSL certificates not found. Generating self-signed certificate..."
    
    # Try to detect the server's external IP
    EXTERNAL_IP=""
    
    # Try multiple methods to get external IP
    for service in "https://api.ipify.org" "https://ifconfig.me/ip" "https://icanhazip.com"; do
        EXTERNAL_IP=$(wget -qO- --timeout=5 "$service" 2>/dev/null | head -1)
        if [ -n "$EXTERNAL_IP" ] && echo "$EXTERNAL_IP" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
            echo "Detected external IP: $EXTERNAL_IP"
            break
        fi
        EXTERNAL_IP=""
    done
    
    # Fallback to hostname if external IP detection fails
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(hostname -i 2>/dev/null | awk '{print $1}')
        if [ -z "$EXTERNAL_IP" ]; then
            EXTERNAL_IP="localhost"
        fi
        echo "Using fallback address: $EXTERNAL_IP"
    fi
    
    # Generate self-signed certificate with the detected IP
    openssl req -x509 -nodes -days 3650 \
        -newkey rsa:2048 \
        -keyout "$SSL_KEY" \
        -out "$SSL_CERT" \
        -subj "/CN=$EXTERNAL_IP/O=Server Manager/OU=Auto Generated" \
        -addext "subjectAltName=IP:$EXTERNAL_IP,DNS:localhost,IP:127.0.0.1" \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "Self-signed SSL certificate generated successfully for $EXTERNAL_IP"
        chmod 600 "$SSL_KEY"
        chmod 644 "$SSL_CERT"
    else
        echo "Warning: Failed to generate SSL certificate. Nginx may fail to start."
    fi
else
    echo "SSL certificates found. Using existing certificates."
fi

# Start nginx
echo "Starting nginx..."
exec nginx -g "daemon off;"
