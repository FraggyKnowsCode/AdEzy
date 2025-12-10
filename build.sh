#!/usr/bin/env bash
# Build script for Render

set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Add categories
python add_categories.py
