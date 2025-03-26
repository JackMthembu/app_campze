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

# Start Gunicorn with more detailed configuration
gunicorn --bind=0.0.0.0:8000 \
         --workers=4 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=debug \
         --capture-output \
         --enable-stdio-inheritance \
         --reload \
         app:app 