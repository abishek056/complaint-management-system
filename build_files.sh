#!/bin/bash

# Install dependencies
pip install -r requirements.txt --break-system-packages

# Collect static files into staticfiles/ (served by WhiteNoise)
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate --noinput
