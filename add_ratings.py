import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adezy.settings')
django.setup()

from marketplace.models import Gig
from decimal import Decimal

# Add ratings to first 4 gigs
gigs = Gig.objects.all()[:4]

ratings_data = [
    {'rating': Decimal('4.8'), 'total_reviews': 23, 'total_orders': 45, 'is_featured': True},
    {'rating': Decimal('4.5'), 'total_reviews': 18, 'total_orders': 32, 'is_featured': True},
    {'rating': Decimal('4.9'), 'total_reviews': 31, 'total_orders': 58, 'is_featured': True},
    {'rating': Decimal('4.3'), 'total_reviews': 12, 'total_orders': 20, 'is_featured': False},
]

for i, gig in enumerate(gigs):
    if i < len(ratings_data):
        gig.rating = ratings_data[i]['rating']
        gig.total_reviews = ratings_data[i]['total_reviews']
        gig.total_orders = ratings_data[i]['total_orders']
        gig.is_featured = ratings_data[i]['is_featured']
        gig.save()
        print(f"✓ Updated {gig.title} - Rating: {gig.rating}, Reviews: {gig.total_reviews}, Featured: {gig.is_featured}")

print(f"\n✓ Successfully added ratings to {len(gigs)} gigs!")
