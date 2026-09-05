#!/bin/bash
echo "=== INSTALLING REQUIREMENTS ==="
python3 -m pip install -r requirements.txt

echo "=== COLLECTING STATIC FILES ==="
python3 manage.py collectstatic --noinput --clear || true

echo "=== ENSURING STATIC ASSETS ==="
mkdir -p staticfiles_build/static
cp -r static/* staticfiles_build/static/ 2>/dev/null || true

echo "=== ENSURING MEDIA ASSETS ==="
mkdir -p staticfiles_build/media
cp -r media/* staticfiles_build/media/ 2>/dev/null || true

echo "=== BUILD FINISHED SUCCESSFULLY ==="
