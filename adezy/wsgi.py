"""
WSGI config for adezy project.
"""

import os

from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adezy.settings')

application = get_wsgi_application()

try:
    from whitenoise import WhiteNoise
    base_dir = Path(__file__).resolve().parent.parent
    staticfiles_dir = base_dir / 'staticfiles_build' / 'static'
    static_dir = base_dir / 'static'
    
    if staticfiles_dir.exists():
        application = WhiteNoise(application, root=str(staticfiles_dir), prefix='static/')
    elif static_dir.exists():
        application = WhiteNoise(application, root=str(static_dir), prefix='static/')
except Exception:
    pass

app = application
