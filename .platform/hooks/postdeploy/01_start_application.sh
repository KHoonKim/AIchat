#!/bin/bash
source /var/app/venv/bin/activate
cd /var/app/current
gunicorn --bind 0.0.0.0:8000 main:app -k uvicorn.workers.UvicornWorker