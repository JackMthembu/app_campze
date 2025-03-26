#!/bin/bash

# Activate the virtual environment if it exists
if [ -d "antenv" ]; then
    source antenv/bin/activate
fi

# Set environment variables
export FLASK_APP=app
export FLASK_ENV=production

# Start Gunicorn
gunicorn --bind=0.0.0.0:8000 \
         --workers=4 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         app:app 