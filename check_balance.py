"""Check user balance"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adezy.settings')
django.setup()

from django.contrib.auth.models import User
from marketplace.models import UserProfile, BalanceRequest

# Check the creativemind user
try:
    user = User.objects.get(username='creativemind')
    profile, created = UserProfile.objects.get_or_create(user=user, defaults={'virtual_credits': 5000.00})
    
    print(f"User: {user.username}")
    print(f"Profile created: {created}")
    print(f"Current balance: {profile.virtual_credits} Taka")
    print(f"\nBalance Requests:")
    
    requests = BalanceRequest.objects.filter(user=user).order_by('-created_at')
    for req in requests:
        print(f"  - {req.amount} Taka | Status: {req.status} | Created: {req.created_at}")
    
    if requests.filter(status='approved').exists():
        approved_total = sum(r.amount for r in requests.filter(status='approved'))
        print(f"\nTotal approved: {approved_total} Taka")
        print(f"Expected balance: {5000 + approved_total} Taka")
        
        if profile.virtual_credits != (5000 + approved_total):
            print(f"\n⚠️ MISMATCH! Fixing balance...")
            profile.virtual_credits = 5000 + approved_total
            profile.save()
            print(f"✓ Balance updated to: {profile.virtual_credits} Taka")
    
except User.DoesNotExist:
    print("User 'creativemind' not found")
