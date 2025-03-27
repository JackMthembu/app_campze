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

# Print environment information
echo "Python version:"
python --version
echo "Current directory:"
pwd
echo "Directory contents:"
ls -la
echo "PYTHONPATH:"
echo $PYTHONPATH

# Ensure required directories exist
mkdir -p /home/site/wwwroot/static
mkdir -p /home/site/wwwroot/templates
mkdir -p /home/site/wwwroot/uploads

# Copy application files to the correct location if needed
if [ -d "/tmp/8dd6d3130a06cf4" ]; then
    cp -r /tmp/8dd6d3130a06cf4/* /home/site/wwwroot/
fi

# Start Gunicorn with production configuration
gunicorn --bind=0.0.0.0:8000 \
         --workers=4 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         --capture-output \
         --enable-stdio-inheritance \
         --static-map /static=/home/site/wwwroot/static \
         --chdir /home/site/wwwroot \
         app:app 