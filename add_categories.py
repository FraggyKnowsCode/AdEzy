"""Script to add default categories to the marketplace"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adezy.settings')
django.setup()

from marketplace.models import Category

# Create categories if they don't exist
categories = [
    {'name': 'Social Media Marketing', 'description': 'Facebook, Instagram, Twitter, LinkedIn ads and promotions', 'icon': 'fa-share-alt'},
    {'name': 'Google Ads', 'description': 'Search ads, display ads, YouTube ads', 'icon': 'fa-google'},
    {'name': 'Content Writing', 'description': 'Ad copy, blog posts, product descriptions', 'icon': 'fa-pen'},
    {'name': 'Graphic Design', 'description': 'Ad banners, social media graphics, logos', 'icon': 'fa-palette'},
    {'name': 'Video Ads', 'description': 'Video production and editing for ads', 'icon': 'fa-video'},
    {'name': 'Email Marketing', 'description': 'Email campaigns and newsletters', 'icon': 'fa-envelope'},
    {'name': 'SEO Services', 'description': 'Search engine optimization and marketing', 'icon': 'fa-search'},
    {'name': 'Analytics & Reports', 'description': 'Ad performance tracking and reporting', 'icon': 'fa-chart-line'},
]

created = 0
for cat_data in categories:
    cat, created_now = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={
            'description': cat_data['description'],
            'icon': cat_data['icon']
        }
    )
    if created_now:
        created += 1
        print(f"✓ Created: {cat.name}")
    else:
        print(f"- Already exists: {cat.name}")

print(f"\n{'='*50}")
print(f"Total categories in database: {Category.objects.count()}")
print(f"Newly created: {created}")
print(f"{'='*50}")
