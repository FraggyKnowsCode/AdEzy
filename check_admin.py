import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adezy.settings')
django.setup()

from django.contrib.auth.models import User

try:
    u = User.objects.get(username='admin')
    print(f"Admin user found:")
    print(f"  - is_staff: {u.is_staff}")
    print(f"  - is_superuser: {u.is_superuser}")
    print(f"  - is_active: {u.is_active}")
    print(f"  - email: {u.email}")
except User.DoesNotExist:
    print("Admin user not found!")
