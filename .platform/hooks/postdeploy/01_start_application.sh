#!/bin/bash
set -e
echo "Activating virtual environment..."
source /var/app/venv/bin/activate
echo "Changing to application directory..."
cd /var/app/current
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 main:app -k uvicorn.workers.UvicornWorker