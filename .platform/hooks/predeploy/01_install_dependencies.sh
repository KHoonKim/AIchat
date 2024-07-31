#!/bin/bash
if [ ! -d "/var/app/venv" ]; then
    python3 -m venv /var/app/venv
fi
source /var/app/venv/bin/activate
pip install --upgrade pip
pip install -r /var/app/staging/requirements.txt
pip install gunicorn