#!/bin/bash

# Exit on error
set -e

# Print commands
set -x

# Install ODBC driver
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

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