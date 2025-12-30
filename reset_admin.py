"""Script to reset admin password"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adezy.settings')
django.setup()

from django.contrib.auth.models import User

# Get or create admin user
try:
    admin = User.objects.get(username='admin')
    print(f"Found existing admin user: {admin.username}")
except User.DoesNotExist:
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@adezy.com',
        password='fahadsikder'
    )
    print(f"Created new admin user: {admin.username}")

# Ensure admin has proper permissions
admin.set_password('fahadsikder')
admin.is_staff = True
admin.is_superuser = True
admin.is_active = True
admin.save()

print(f"""
✓ Admin account configured successfully!

Login Credentials:
==================
Username: admin
Password: fahadsikder
URL: http://localhost:8000/admin/

Permissions:
- is_staff: {admin.is_staff}
- is_superuser: {admin.is_superuser}
- is_active: {admin.is_active}
""")
