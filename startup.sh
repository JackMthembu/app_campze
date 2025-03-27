#!/bin/bash

# Exit on error
set -e

# Print commands
set -x

# Install MySQL client libraries and dependencies
apt-get update
apt-get install -y default-libmysqlclient-dev build-essential pkg-config python3-dev default-mysql-client

# Activate the virtual environment if it exists
if [ -d "antenv" ]; then
    source antenv/bin/activate
fi

# Set environment variables
export FLASK_APP=app
export FLASK_ENV=production
export PYTHONPATH=/home/site/wwwroot
export PORT=8181

# Print environment information
echo "Python version:"
python --version
echo "Current directory:"
pwd
echo "Directory contents:"
ls -la
echo "PYTHONPATH:"
echo $PYTHONPATH

# Find the temporary directory containing the application
TEMP_DIR=$(find /tmp -maxdepth 1 -type d -name "8dd6d*" | head -n 1)
if [ -z "$TEMP_DIR" ]; then
    echo "Error: Could not find temporary directory"
    exit 1
fi

echo "Found temporary directory: $TEMP_DIR"

# Create required directories
mkdir -p /home/site/wwwroot/static
mkdir -p /home/site/wwwroot/templates
mkdir -p /home/site/wwwroot/uploads

# Copy application files to the correct location
echo "Copying application files..."
cp -r $TEMP_DIR/* /home/site/wwwroot/

# Verify the files were copied
echo "Verifying files in wwwroot:"
ls -la /home/site/wwwroot/

# Start Gunicorn with production configuration
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