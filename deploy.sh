#!/bin/bash

# Exit on error
set -e

# Print commands
set -x

# Wait for any pending operations to complete
echo "Waiting for any pending operations to complete..."
sleep 30

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p /home/site/wwwroot/static
mkdir -p /home/site/wwwroot/templates
mkdir -p /home/site/wwwroot/uploads

# Copy application files
echo "Copying application files..."
cp -r . /home/site/wwwroot/

# Set permissions
echo "Setting permissions..."
chmod -R 755 /home/site/wwwroot

# Wait for file system operations to complete
echo "Waiting for file system operations to complete..."
sleep 10

# Start the application
echo "Starting the application..."
gunicorn --bind=0.0.0.0:$PORT \
         --workers=4 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         --capture-output \
         --enable-stdio-inheritance \
         --static-map /static=/home/site/wwwroot/static \
         --chdir /home/site/wwwroot \
         --forwarded-allow-ips="*" \
         --proxy-allow-ips="*" \
         app:app 