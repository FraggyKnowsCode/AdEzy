"""
AdEzy - Admin Password Reset Utility
Run this anytime you forget or need to reset the admin password:
    python reset_admin.py
or with a custom password:
    python reset_admin.py mynewpassword
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adezy.settings')
django.setup()

from django.contrib.auth.models import User

# Password to set (default is 'fahadsikder' unless specified as argument)
password = sys.argv[1] if len(sys.argv) > 1 else 'fahadsikder'

admin, created = User.objects.get_or_create(
    username='admin',
    defaults={'email': 'admin@adezy.com'}
)

admin.set_password(password)
admin.is_staff = True
admin.is_superuser = True
admin.is_active = True
admin.save()

action_str = "Created new" if created else "Updated existing"
print(f"""
========================================
  AdEzy Admin Credentials
========================================
  Status:   {action_str} superuser account
  Username: admin
  Password: {password}
  Admin URL: http://127.0.0.1:8000/admin/
========================================
[OK] You can now log into the Django Admin!
""")
