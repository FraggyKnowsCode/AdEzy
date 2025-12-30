"""Script to populate the database with 30 sample gigs with images"""
import os
import django
import random
from django.core.files.base import ContentFile
import requests
from io import BytesIO

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adezy.settings')
django.setup()

from django.contrib.auth.models import User
from marketplace.models import Gig, Category, UserProfile

# Sample gig data for different categories
GIG_TEMPLATES = {
    'Social Media Marketing': [
        {
            'title': 'I will create and manage your Instagram ad campaign',
            'description': 'Professional Instagram advertising service with targeted audience reach. I will set up, optimize, and manage your Instagram ad campaigns for maximum ROI. Includes audience research, creative strategy, and performance monitoring.',
            'price_range': (50, 200),
            'delivery_range': (3, 7)
        },
        {
            'title': 'I will run Facebook ads for your business',
            'description': 'Get more customers with expertly managed Facebook ads. I specialize in conversion-focused campaigns that drive real results. Services include ad creation, A/B testing, and detailed analytics reports.',
            'price_range': (75, 250),
            'delivery_range': (5, 10)
        },
        {
            'title': 'I will grow your social media presence organically',
            'description': 'Increase your followers and engagement with proven organic growth strategies. No bots, just real followers who are interested in your content. Includes content planning and engagement tactics.',
            'price_range': (100, 300),
            'delivery_range': (7, 14)
        },
        {
            'title': 'I will create viral TikTok ad campaigns',
            'description': 'Expert TikTok advertising that reaches your target audience. I create engaging ads that resonate with TikTok users and drive conversions. Includes creative development and campaign optimization.',
            'price_range': (80, 220),
            'delivery_range': (4, 8)
        },
    ],
    'Google Ads': [
        {
            'title': 'I will setup and manage your Google Ads campaigns',
            'description': 'Professional Google Ads management service. I will create high-converting search campaigns, optimize your keywords, and maximize your ad spend efficiency. Includes keyword research and bid optimization.',
            'price_range': (100, 350),
            'delivery_range': (5, 10)
        },
        {
            'title': 'I will optimize your Google Shopping ads',
            'description': 'Increase your ecommerce sales with optimized Google Shopping campaigns. I will set up product feeds, optimize bids, and improve your ROAS. Perfect for online stores.',
            'price_range': (120, 400),
            'delivery_range': (7, 14)
        },
        {
            'title': 'I will create YouTube ad campaigns that convert',
            'description': 'Expert YouTube advertising service for maximum reach. I create compelling video ad campaigns that engage viewers and drive actions. Includes targeting strategy and performance tracking.',
            'price_range': (150, 450),
            'delivery_range': (7, 14)
        },
    ],
    'Content Writing': [
        {
            'title': 'I will write compelling ad copy for your campaigns',
            'description': 'High-converting ad copy that sells. I write persuasive headlines and descriptions that grab attention and drive clicks. Experienced in all ad platforms including Google, Facebook, and Instagram.',
            'price_range': (30, 100),
            'delivery_range': (2, 5)
        },
        {
            'title': 'I will create SEO blog posts for your website',
            'description': 'Well-researched, SEO-optimized blog content that ranks. I write engaging articles that attract organic traffic and establish your authority. Includes keyword optimization and meta descriptions.',
            'price_range': (50, 150),
            'delivery_range': (3, 7)
        },
        {
            'title': 'I will write product descriptions that sell',
            'description': 'Compelling product descriptions that convert browsers into buyers. I highlight benefits, create urgency, and overcome objections. Perfect for ecommerce stores and marketplaces.',
            'price_range': (25, 80),
            'delivery_range': (2, 4)
        },
        {
            'title': 'I will create email marketing copy that converts',
            'description': 'Persuasive email copy that drives opens, clicks, and sales. I write subject lines and body copy that engages your audience and prompts action. Includes A/B testing recommendations.',
            'price_range': (40, 120),
            'delivery_range': (3, 5)
        },
    ],
    'Graphic Design': [
        {
            'title': 'I will design professional ad banners',
            'description': 'Eye-catching banner ads for all your campaigns. I create designs that grab attention and drive clicks. Includes multiple size variations and unlimited revisions until you are satisfied.',
            'price_range': (35, 120),
            'delivery_range': (2, 5)
        },
        {
            'title': 'I will create social media graphics',
            'description': 'Professional social media graphics for Instagram, Facebook, and more. I design on-brand visuals that stop the scroll and engage your audience. Includes templates for easy future use.',
            'price_range': (45, 150),
            'delivery_range': (3, 7)
        },
        {
            'title': 'I will design a modern logo for your brand',
            'description': 'Unique logo design that represents your brand perfectly. I create memorable logos with multiple concepts and revisions. Includes all source files and various format exports.',
            'price_range': (80, 300),
            'delivery_range': (5, 10)
        },
        {
            'title': 'I will design Instagram story templates',
            'description': 'Beautiful Instagram story templates for your business. Fully customizable designs that maintain your brand consistency. Includes 10+ unique template variations.',
            'price_range': (50, 180),
            'delivery_range': (3, 7)
        },
    ],
    'Video Ads': [
        {
            'title': 'I will create engaging video ads for social media',
            'description': 'Professional video ads that capture attention in the first 3 seconds. I create scroll-stopping videos optimized for Facebook, Instagram, and TikTok. Includes motion graphics and sound design.',
            'price_range': (150, 500),
            'delivery_range': (7, 14)
        },
        {
            'title': 'I will edit your video ad for maximum impact',
            'description': 'Expert video editing that tells your brand story. I transform raw footage into compelling video ads with professional transitions, color grading, and sound. Fast turnaround guaranteed.',
            'price_range': (100, 350),
            'delivery_range': (5, 10)
        },
        {
            'title': 'I will create animated explainer videos',
            'description': 'Animated videos that explain your product or service clearly. Perfect for ads, websites, and presentations. I create engaging animations that simplify complex ideas.',
            'price_range': (200, 600),
            'delivery_range': (10, 21)
        },
    ],
    'Email Marketing': [
        {
            'title': 'I will design email templates for your campaigns',
            'description': 'Responsive email templates that look great on all devices. I create branded designs that drive engagement and conversions. Includes mobile optimization and testing.',
            'price_range': (60, 200),
            'delivery_range': (3, 7)
        },
        {
            'title': 'I will setup email automation for your business',
            'description': 'Automated email sequences that nurture leads and drive sales. I set up welcome series, abandoned cart emails, and promotional campaigns. Includes strategy and copywriting.',
            'price_range': (120, 400),
            'delivery_range': (7, 14)
        },
    ],
    'SEO Services': [
        {
            'title': 'I will do complete SEO optimization for your website',
            'description': 'Comprehensive SEO service to improve your search rankings. Includes on-page optimization, technical SEO audit, and keyword strategy. Get more organic traffic and leads.',
            'price_range': (100, 400),
            'delivery_range': (7, 14)
        },
        {
            'title': 'I will create high-quality backlinks for your site',
            'description': 'White-hat link building that improves your domain authority. I secure quality backlinks from relevant, high-authority websites. Safe and Google-compliant methods only.',
            'price_range': (80, 300),
            'delivery_range': (10, 21)
        },
        {
            'title': 'I will do keyword research for your niche',
            'description': 'In-depth keyword research to find profitable opportunities. I identify low-competition, high-volume keywords you can rank for. Includes search intent analysis and competitor research.',
            'price_range': (50, 150),
            'delivery_range': (3, 5)
        },
    ],
    'Analytics & Reports': [
        {
            'title': 'I will setup Google Analytics for your website',
            'description': 'Complete Google Analytics setup and configuration. I install tracking codes, set up goals, and create custom dashboards. Includes training on how to read your data.',
            'price_range': (70, 200),
            'delivery_range': (3, 7)
        },
        {
            'title': 'I will create ad performance reports',
            'description': 'Professional ad performance reports with actionable insights. I analyze your campaigns across all platforms and provide recommendations for improvement. Includes visualizations and data analysis.',
            'price_range': (80, 250),
            'delivery_range': (5, 10)
        },
    ],
}

def download_placeholder_image(width=800, height=600, seed=None):
    """Download a placeholder image from Picsum"""
    try:
        # Using Lorem Picsum for placeholder images
        url = f"https://picsum.photos/{width}/{height}"
        if seed:
            url += f"?random={seed}"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return ContentFile(response.content, name=f'gig_{seed}.jpg')
        else:
            print(f"Failed to download image: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def create_sample_sellers(count=10):
    """Create sample seller accounts"""
    sellers = []
    seller_names = [
        'marketingpro', 'designwizard', 'adsguru', 'contentking',
        'videomaster', 'seoexpert', 'socialmaven', 'analyticsninja',
        'creativemind', 'digitalgenius', 'adspecialist', 'growthhacker'
    ]
    
    for i, username in enumerate(seller_names[:count]):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': username.capitalize(),
                'is_active': True
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✓ Created seller: {username}")
        
        # Create or get profile and set to seller mode
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_seller_mode = True
        profile.bio = f"Professional {username} with years of experience in digital marketing and advertising."
        profile.save()
        
        sellers.append(user)
    
    return sellers

def populate_gigs(count=30):
    """Create sample gigs with images"""
    print("Starting gig population...")
    print("="*60)
    
    # Ensure we have categories
    categories = list(Category.objects.all())
    if not categories:
        print("❌ No categories found! Please run add_categories.py first.")
        return
    
    print(f"Found {len(categories)} categories")
    
    # Create sellers
    print("\nCreating sample sellers...")
    sellers = create_sample_sellers(10)
    print(f"✓ Ready with {len(sellers)} sellers")
    
    # Clear existing gigs (optional - comment out if you want to keep existing)
    # Gig.objects.all().delete()
    # print("Cleared existing gigs")
    
    print(f"\nCreating {count} gigs with images...")
    print("-"*60)
    
    created_count = 0
    
    for i in range(count):
        # Pick a random category
        category = random.choice(categories)
        
        # Get templates for this category
        templates = GIG_TEMPLATES.get(category.name, [])
        if not templates:
            # Fallback for categories without templates
            templates = [{
                'title': f'I will provide {category.name.lower()} services',
                'description': f'Professional {category.name.lower()} services to help grow your business. High quality work with fast delivery.',
                'price_range': (50, 200),
                'delivery_range': (3, 7)
            }]
        
        # Select a random template
        template = random.choice(templates)
        
        # Randomize pricing and delivery
        price = random.randint(template['price_range'][0], template['price_range'][1])
        delivery_time = random.randint(template['delivery_range'][0], template['delivery_range'][1])
        
        # Select a random seller
        seller = random.choice(sellers)
        
        # Download placeholder image
        print(f"[{i+1}/{count}] Creating: {template['title'][:50]}...")
        image_file = download_placeholder_image(seed=1000+i)
        
        # Create the gig
        try:
            gig = Gig.objects.create(
                seller=seller,
                title=template['title'],
                description=template['description'],
                category=category,
                price=price,
                delivery_time=delivery_time,
                status='active'
            )
            
            # Attach image if downloaded successfully
            if image_file:
                gig.image.save(f'gig_{i+1}.jpg', image_file, save=True)
                print(f"  ✓ Created with image | ${price} | {delivery_time} days | {category.name}")
            else:
                print(f"  ⚠ Created without image | ${price} | {delivery_time} days | {category.name}")
            
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Error creating gig: {e}")
    
    print("="*60)
    print(f"\n🎉 Successfully created {created_count} gigs!")
    print(f"Total gigs in database: {Gig.objects.count()}")
    print("\nBreakdown by category:")
    for cat in categories:
        count = cat.gigs.count()
        print(f"  - {cat.name}: {count} gigs")

if __name__ == '__main__':
    try:
        populate_gigs(30)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
