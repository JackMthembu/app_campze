#!/bin/bash

# Exit on error
set -e

# Print commands
set -x

# Set environment variables
export FLASK_APP=app
export FLASK_ENV=production
export PYTHONPATH=/home/site/wwwroot

# Debug: Print environment variables
echo "Current environment variables:"
echo "FLASK_APP=$FLASK_APP"
echo "FLASK_ENV=$FLASK_ENV"
echo "PYTHONPATH=$PYTHONPATH"

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
cp -r ./* /home/site/wwwroot/

# Set permissions
echo "Setting permissions..."
chmod -R 755 /home/site/wwwroot

# Wait for file system operations to complete
echo "Waiting for file system operations to complete..."
sleep 10

# Start the application with Gunicorn
echo "Starting the application on port 8181..."
exec gunicorn --bind=0.0.0.0:8181 \
    --workers=4 \
    --timeout=120 \
    --access-logfile=- \
    --error-logfile=- \
    --capture-output \
    --enable-stdio-inheritance \
    --preload \
    --log-level=debug \
    app:app 