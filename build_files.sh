#!/bin/bash
pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
mkdir -p staticfiles_build/media
cp -r media/* staticfiles_build/media/ 2>/dev/null || true
