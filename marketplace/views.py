from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404, HttpResponse
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Gig, Order, UserProfile, Category, Transaction, Message, BalanceRequest, CashoutRequest, Notification
from .products_data import get_all_products, get_product_by_id, get_related_products
import json
import os
import requests
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
from django.core.files.base import ContentFile
from openai import OpenAI
from .supabase_auth import (
    create_or_update_supabase_auth_user,
    update_supabase_password,
    verify_supabase_user
)

def home(request):
    """Render the home page (HTML skeleton)"""
    return render(request, 'marketplace/home.html')

def services_page(request):
    """Render dedicated Services marketplace page"""
    categories = Category.objects.all()
    return render(request, 'marketplace/services.html', {'categories': categories})

def products_page(request):
    """Render dedicated Products catalog page with categorized filters"""
    products = get_all_products()
    return render(request, 'marketplace/products.html', {'products': products})

def product_detail_page(request, product_id):
    """Render dedicated Digital Product detail page"""
    product = get_product_by_id(product_id)
    if not product:
        raise Http404("Product not found")
    related_products = get_related_products(product_id, limit=4)
    return render(request, 'marketplace/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'product_id': product_id
    })

def about_page(request):
    """Render dedicated About Us page"""
    return render(request, 'marketplace/about.html')

def reviews_page(request):
    """Render dedicated Client Reviews page"""
    return render(request, 'marketplace/reviews.html')

def blog_page(request):
    """Render dedicated Blog and Growth resources page"""
    return render(request, 'marketplace/blog.html')

def login_view(request):
    """Handle user login with username or email, integrating Supabase Auth"""
    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Support login by email or username
        if '@' in login_input:
            user_obj = User.objects.filter(email__iexact=login_input).first()
            username = user_obj.username if user_obj else login_input
        else:
            username = login_input

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            # Update Supabase Auth last sign in
            verify_supabase_user(user.email or user.username, password)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username/email or password')
    
    return render(request, 'marketplace/login.html')

def logout_view(request):
    """Handle user logout"""
    auth_logout(request)
    return redirect('home')

def register_view(request):
    """Handle user registration and sync directly with Supabase Auth"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        
        if not email:
            messages.error(request, 'Email address is required for registration')
        elif password != password2:
            messages.error(request, 'Passwords do not match')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Username already exists')
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email already registered')
        else:
            # 1. Register in Supabase Auth (auth.users)
            success, err, _ = create_or_update_supabase_auth_user(email=email, password=password, username=username)
            if not success:
                messages.error(request, f'Failed to create account in Supabase: {err}')
                return render(request, 'marketplace/register.html')

            # 2. Create Django User & Profile
            user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user, virtual_credits=5000.00)
            auth_login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    
    return render(request, 'marketplace/register.html')

def gig_detail(request, gig_id):
    """Render the gig detail page"""
    gig = get_object_or_404(Gig, id=gig_id, status='active')
    return render(request, 'marketplace/gig_detail.html', {'gig': gig, 'gig_id': gig_id})

@login_required
def profile(request):
    """Handle user profile page and updates"""
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'virtual_credits': 5000.00}
    )
    
    if request.method == 'POST':
        # Update user information
        username = request.POST.get('username')
        email = request.POST.get('email')
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')
        
        # Check if username is taken by another user
        if username != request.user.username and User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
        elif email != request.user.email and User.objects.filter(email=email).exists():
            messages.error(request, 'Email already in use')
        else:
            # Update username and email
            request.user.username = username
            request.user.email = email
            request.user.save()
            
            # Update password if provided
            if current_password and new_password:
                if not request.user.check_password(current_password):
                    messages.error(request, 'Current password is incorrect')
                elif new_password != new_password2:
                    messages.error(request, 'New passwords do not match')
                elif len(new_password) < 6:
                    messages.error(request, 'Password must be at least 6 characters')
                else:
                    request.user.set_password(new_password)
                    request.user.save()
                    update_supabase_password(request.user.email, new_password)
                    auth_login(request, request.user)  # Re-login after password change
                    messages.success(request, 'Password updated successfully!')
                    return redirect('profile')
            
            # Sync username/email update to Supabase Auth metadata
            create_or_update_supabase_auth_user(
                email=request.user.email,
                password="",
                username=request.user.username,
                display_name=request.user.get_full_name()
            )
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    
    return render(request, 'marketplace/profile.html')

def css_showcase(request):
    """Render the CSS showcase page"""
    return render(request, 'marketplace/css_showcase.html')

def get_all_gigs_json(request):
    """
    API endpoint: Return all active gigs as JSON with filtering support
    URL: /api/gigs/
    Query Parameters:
    - category: Filter by category name
    - filter: 'top-rated', 'new', or 'all' (default)
    Note: Gigs remain available regardless of order status.
    Users can order the same gig multiple times.
    """
    gigs = Gig.objects.filter(status='active').select_related('seller', 'category')
    
    # Category filtering
    category_filter = request.GET.get('category', None)
    if category_filter:
        gigs = gigs.filter(category__name__iexact=category_filter)
    
    # Filter by type
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'top-rated':
        # Filter gigs with rating >= 4.5 or is_featured=True
        gigs = gigs.filter(is_featured=True).order_by('-rating', '-total_orders')
    elif filter_type == 'new':
        # Get gigs created in last 30 days
        from datetime import timedelta
        from django.utils import timezone
        thirty_days_ago = timezone.now() - timedelta(days=30)
        gigs = gigs.filter(created_at__gte=thirty_days_ago).order_by('-created_at')
    
    gigs_data = []
    for gig in gigs:
        gigs_data.append({
            'id': gig.id,
            'title': gig.title,
            'price': float(gig.price),
            'image_url': gig.image.url if gig.image else '/static/images/default-gig.jpg',
            'seller_name': gig.seller.username,
            'category': gig.category.name if gig.category else 'Uncategorized',
            'delivery_time': gig.delivery_time,
            'description': gig.description[:100] + '...' if len(gig.description) > 100 else gig.description,
            'rating': float(gig.rating) if gig.rating else 0,
            'total_reviews': gig.total_reviews,
            'total_orders': gig.total_orders,
            'is_featured': gig.is_featured,
            'created_at': gig.created_at.isoformat(),
        })
    
    return JsonResponse({'gigs': gigs_data}, safe=False)


def get_gig_detail_json(request, gig_id):
    """
    API endpoint: Return single gig details as JSON
    URL: /api/gigs/<id>/
    """
    gig = get_object_or_404(Gig, id=gig_id, status='active')
    
    gig_data = {
        'id': gig.id,
        'title': gig.title,
        'description': gig.description,
        'price': float(gig.price),
        'image_url': gig.image.url if gig.image else '/static/images/default-gig.jpg',
        'seller_name': gig.seller.username,
        'seller_id': gig.seller.id,
        'category': gig.category.name if gig.category else 'Uncategorized',
        'delivery_time': gig.delivery_time,
        'created_at': gig.created_at.isoformat(),
    }
    
    return JsonResponse(gig_data)


@login_required
@require_http_methods(["POST"])
def create_order_json(request):
    """
    API endpoint: Create a new order
    URL: /api/orders/create/
    Expected POST data: {gig_id: int, requirements: string (optional)}
    """
    try:
        data = json.loads(request.body)
        gig_id = data.get('gig_id')
        requirements = data.get('requirements', '')
        
        # Get the gig
        gig = get_object_or_404(Gig, id=gig_id, status='active')
        
        # Get buyer profile
        buyer_profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'virtual_credits': 5000.00}
        )
        
        # Check if user has enough credits
        if buyer_profile.virtual_credits < gig.price:
            return JsonResponse({
                'success': False,
                'error': f'Insufficient balance. You need ৳ {gig.price} BDT, but have ৳ {buyer_profile.virtual_credits} BDT.'
            }, status=400)
        
        # Check if buyer is trying to buy their own gig
        if gig.seller == request.user:
            return JsonResponse({
                'success': False,
                'error': 'You cannot order your own gig'
            }, status=400)
        
        # Create order with transaction
        with transaction.atomic():
            # Deduct credits from buyer
            buyer_profile.virtual_credits -= gig.price
            buyer_profile.save()
            
            # Create order (pending)
            order = Order.objects.create(
                gig=gig,
                buyer=request.user,
                seller=gig.seller,
                price=gig.price,
                requirements=requirements,
                status='pending'
            )
            
            # Create debit transaction record for buyer
            Transaction.objects.create(
                user=request.user,
                transaction_type='debit',
                amount=gig.price,
                balance_after=buyer_profile.virtual_credits,
                description=f"Purchase: {gig.title}",
                order=order
            )
            
            # Create notification for seller
            from .models import Notification
            Notification.objects.create(
                user=gig.seller,
                notification_type='order_placed',
                title='New Order Received',
                message=f"{request.user.username} placed an order for {gig.title}",
                order=order
            )
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'new_balance': float(buyer_profile.virtual_credits),
            'message': 'Order placed successfully!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def checkout_cart_json(request):
    """
    API endpoint: Batch checkout shopping cart items (services + digital products)
    URL: /api/cart/checkout/
    """
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        if not items:
            return JsonResponse({'success': False, 'error': 'Your cart is empty.'}, status=400)

        total_price = sum(Decimal(str(item.get('price', 0))) for item in items)

        buyer_profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'virtual_credits': 5000.00}
        )

        if buyer_profile.virtual_credits < total_price:
            return JsonResponse({
                'success': False,
                'error': f'Insufficient balance. Cart total is {total_price:.2f} ৳, but your balance is {buyer_profile.virtual_credits:.2f} ৳.'
            }, status=400)

        created_orders = []
        purchased_products = []

        with transaction.atomic():
            for item in items:
                item_type = item.get('type', 'service')
                item_id = item.get('id')
                item_price = Decimal(str(item.get('price', 0)))
                item_title = item.get('title', 'Item')

                if item_type == 'service':
                    gig = Gig.objects.filter(id=int(item_id), status='active').first()
                    if not gig:
                        continue
                    if gig.seller == request.user:
                        return JsonResponse({
                            'success': False,
                            'error': f'You cannot order your own service: "{gig.title}"'
                        }, status=400)

                    # Deduct credits from buyer
                    buyer_profile.virtual_credits -= item_price
                    buyer_profile.save()

                    # Create gig order (pending)
                    order = Order.objects.create(
                        gig=gig,
                        buyer=request.user,
                        seller=gig.seller,
                        price=item_price,
                        requirements='Order placed through AdEzy Cart Checkout',
                        status='pending'
                    )

                    # Debit transaction record for buyer
                    Transaction.objects.create(
                        user=request.user,
                        transaction_type='debit',
                        amount=item_price,
                        balance_after=buyer_profile.virtual_credits,
                        description=f"Purchase: {gig.title}",
                        order=order
                    )

                    # Seller notification
                    Notification.objects.create(
                        user=gig.seller,
                        notification_type='order_placed',
                        title='New Order Placed',
                        message=f"{request.user.username} ordered {gig.title} via Cart",
                        order=order
                    )

                    created_orders.append({
                        'id': order.id,
                        'title': gig.title,
                        'price': float(item_price),
                        'delivery_time': gig.delivery_time
                    })

                else:
                    # Digital product purchase
                    buyer_profile.virtual_credits -= item_price
                    buyer_profile.save()

                    Transaction.objects.create(
                        user=request.user,
                        transaction_type='debit',
                        amount=item_price,
                        balance_after=buyer_profile.virtual_credits,
                        description=f"Digital Product: {item_title}"
                    )

                    purchased_products.append({
                        'id': item_id,
                        'title': item_title,
                        'price': float(item_price),
                        'download_url': f"/api/product/{item_id}/download/"
                    })

        return JsonResponse({
            'success': True,
            'message': 'Cart purchase completed successfully!',
            'new_balance': float(buyer_profile.virtual_credits),
            'orders': created_orders,
            'products': purchased_products
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def download_product_api(request, product_id):
    """
    Download digital product license and package starter
    """
    product = get_product_by_id(product_id)
    if not product:
        raise Http404("Product not found")

    content = f"""===================================================================
AdEzy Digital Product Delivery & Verification
===================================================================
Product:       {product['title']}
Category:      {product['category_label']}
Licensee:      {request.user.username} ({request.user.email})
License Key:   ADZY-{request.user.id:04d}-{product_id.upper()}-VERIFIED
File Specs:    {product['file_size']} | {product['file_format']}
Timestamp:     {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

WHAT'S INCLUDED:
{chr(10).join('- ' + f for f in product['features'])}

ACCESS & CLOUD DOWNLOAD:
Your complete package has been prepared on our high-speed CDN.
Access link: https://cdn.adezy.com/packages/{product_id}/full-bundle.zip
(All future updates are automatically pushed to this access key)

Need help? Contact Priority Creator Support: support@adezy.com
All rights reserved by Fahad Sidker.
===================================================================
"""
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="AdEzy-{product_id}-Package.txt"'
    return response


@login_required
def get_user_balance_json(request):
    """
    API endpoint: Get current user's virtual credit balance and seller earnings
    URL: /api/user/balance/
    """
    from django.db.models import Sum
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'virtual_credits': 5000.00}
    )
    
    # Calculate seller earnings from completed orders
    total_earnings = Order.objects.filter(
        seller=request.user,
        status='completed'
    ).aggregate(total=Sum('price'))['total'] or 0
    
    total_cashed_out = CashoutRequest.objects.filter(
        user=request.user,
        status='approved'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    available_earnings = float(total_earnings) - float(total_cashed_out)

    return JsonResponse({
        'balance': float(profile.virtual_credits),
        'earnings': available_earnings,
        'total_earnings': float(total_earnings),
        'username': request.user.username
    })


@login_required
def get_buyer_orders_json(request):
    """
    API endpoint: Get all orders for the current user as buyer
    URL: /api/orders/buyer/
    """
    orders = Order.objects.filter(buyer=request.user).select_related('gig', 'seller')
    
    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'gig_title': order.gig.title,
            'seller_name': order.seller.username,
            'price': float(order.price),
            'status': order.status,
            'created_at': order.created_at.isoformat(),
            'delivery_time': order.gig.delivery_time,
        })
    
    return JsonResponse({'orders': orders_data})


@login_required
def get_seller_orders_json(request):
    """
    API endpoint: Get all orders for the current user as seller
    URL: /api/orders/seller/
    """
    orders = Order.objects.filter(seller=request.user).select_related('gig', 'buyer')
    
    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'gig_title': order.gig.title,
            'buyer_name': order.buyer.username,
            'price': float(order.price),
            'status': order.status,
            'created_at': order.created_at.isoformat(),
            'requirements': order.requirements,
        })
    
    return JsonResponse({'orders': orders_data})


@login_required
def dashboard(request):
    """Render the dashboard page (HTML skeleton)"""
    return render(request, 'marketplace/dashboard.html')

@login_required
def create_gig(request):
    """Create a new gig"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        delivery_time = request.POST.get('delivery_time')
        image = request.FILES.get('image')
        
        try:
            category = Category.objects.get(id=category_id) if category_id else None
            
            gig = Gig.objects.create(
                seller=request.user,
                title=title,
                description=description,
                category=category,
                price=price,
                delivery_time=delivery_time,
                image=image,
                status='active'
            )
            
            # Ensure user has a profile
            if not hasattr(request.user, 'profile'):
                UserProfile.objects.create(user=request.user, virtual_credits=5000.00)
            
            messages.success(request, 'Gig created successfully!')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error creating gig: {str(e)}')
    
    categories = Category.objects.all()
    return render(request, 'marketplace/create_gig.html', {'categories': categories})

@login_required
def update_gig(request, gig_id):
    """Update an existing gig"""
    gig = get_object_or_404(Gig, id=gig_id, seller=request.user)
    
    if request.method == 'POST':
        gig.title = request.POST.get('title')
        gig.description = request.POST.get('description')
        category_id = request.POST.get('category')
        gig.price = request.POST.get('price')
        gig.delivery_time = request.POST.get('delivery_time')
        
        # Update image if new one is provided
        if request.FILES.get('image'):
            gig.image = request.FILES.get('image')
        
        if category_id:
            gig.category = Category.objects.get(id=category_id)
        
        gig.save()
        messages.success(request, 'Gig updated successfully!')
        return redirect('dashboard')
    
    categories = Category.objects.all()
    return render(request, 'marketplace/update_gig.html', {
        'gig': gig,
        'categories': categories
    })

@login_required
def imagine_view(request):
    """Render the AI poster generator page"""
    return render(request, 'marketplace/imagine.html')

@login_required
def generate_poster_api(request):
    """Generate poster using AI - currently unavailable due to maintenance"""
    return JsonResponse({
        'success': False,
        'error': 'AI Imagine services are temporarily unavailable as the AI API is undergoing maintenance. Please check back soon.'
    }, status=503)

def create_poster_image(product_image, logo_image, description):
    """Create a beautiful poster with product image and logo"""
    # Open product image
    product = Image.open(product_image).convert('RGBA')
    
    # Create canvas (Instagram square format)
    canvas_width, canvas_height = 1080, 1080
    canvas = Image.new('RGB', (canvas_width, canvas_height), '#ffffff')
    
    # Resize product image to fit nicely
    product_width = int(canvas_width * 0.8)
    product_height = int(canvas_height * 0.7)
    product.thumbnail((product_width, product_height), Image.Resampling.LANCZOS)
    
    # Calculate position to center product
    product_x = (canvas_width - product.width) // 2
    product_y = (canvas_height - product.height) // 2 - 50
    
    # Create gradient background
    draw = ImageDraw.Draw(canvas)
    for i in range(canvas_height):
        alpha = i / canvas_height
        r = int(255 * (1 - alpha) + 240 * alpha)
        g = int(250 * (1 - alpha) + 200 * alpha)
        b = int(255 * (1 - alpha) + 150 * alpha)
        draw.rectangle([(0, i), (canvas_width, i+1)], fill=(r, g, b))
    
    # Add shadow behind product
    shadow = Image.new('RGBA', product.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rectangle([0, 0, product.width, product.height], fill=(0, 0, 0, 100))
    shadow = shadow.blur_image(shadow, 20)
    canvas.paste(shadow, (product_x + 10, product_y + 10), shadow)
    
    # Paste product image
    if product.mode == 'RGBA':
        canvas.paste(product, (product_x, product_y), product)
    else:
        canvas.paste(product, (product_x, product_y))
    
    # Add logo if provided
    if logo_image:
        logo = Image.open(logo_image).convert('RGBA')
        logo_size = 150
        logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
        logo_x = canvas_width - logo.width - 40
        logo_y = 40
        canvas.paste(logo, (logo_x, logo_y), logo)
    
    # Add decorative elements
    draw = ImageDraw.Draw(canvas)
    
    # Top banner
    draw.rectangle([(0, 0), (canvas_width, 100)], fill=(16, 24, 40, 200))
    
    # Bottom banner
    draw.rectangle([(0, canvas_height - 100), (canvas_width, canvas_height)], fill=(16, 24, 40, 200))
    
    return canvas

def blur_image(image, radius):
    """Apply blur filter to image"""
    return image.filter(ImageFilter.GaussianBlur(radius))

@login_required
def get_my_gigs_json(request):
    """API endpoint: Return current user's gigs as JSON"""
    gigs = Gig.objects.filter(seller=request.user).select_related('category')
    
    gigs_data = []
    for gig in gigs:
        gigs_data.append({
            'id': gig.id,
            'title': gig.title,
            'price': float(gig.price),
            'image_url': gig.image.url if gig.image else '/static/images/default-gig.jpg',
            'category': gig.category.name if gig.category else 'Uncategorized',
            'delivery_time': gig.delivery_time,
            'status': gig.status,
            'created_at': gig.created_at.strftime('%Y-%m-%d'),
        })
    
    return JsonResponse({'gigs': gigs_data})

@login_required
@require_http_methods(["POST"])
def update_order_status_json(request, order_id):
    """Update order status (sellers can accept/deliver, buyers can complete)"""
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        # Get order - check if user is buyer or seller
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Order not found'
            }, status=404)
        
        # Verify user is part of the order
        if request.user != order.seller and request.user != order.buyer:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to update this order'
            }, status=403)
        
        # Sellers can: accept (in_progress), deliver (delivered), cancel
        # Buyers can: complete (completed)
        if new_status == 'completed':
            # Only buyer can mark as completed
            if request.user != order.buyer:
                return JsonResponse({
                    'success': False,
                    'error': 'Only the buyer can mark the order as completed'
                }, status=403)
            # Order must be delivered before completion
            if order.status != 'delivered':
                return JsonResponse({
                    'success': False,
                    'error': 'Order must be delivered before completion'
                }, status=400)
        elif new_status in ['in_progress', 'delivered', 'cancelled']:
            # Only seller can change these statuses
            if request.user != order.seller:
                return JsonResponse({
                    'success': False,
                    'error': 'Only the seller can update this status'
                }, status=403)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid status'
            }, status=400)
        
        # Update order status
        order.status = new_status
        if new_status == 'completed':
            order.completed_at = timezone.now()
            # Record earning transaction for the seller
            seller_profile, _ = UserProfile.objects.get_or_create(
                user=order.seller,
                defaults={'virtual_credits': 5000.00}
            )
            Transaction.objects.create(
                user=order.seller,
                transaction_type='earning',
                amount=order.price,
                balance_after=seller_profile.virtual_credits,  # Credits balance unchanged; earnings updated
                description=f"Earnings from completed Order #{order.id}: {order.gig.title}",
                order=order
            )
            if order.gig:
                order.gig.total_orders = (order.gig.total_orders or 0) + 1
                order.gig.save()
        elif new_status == 'cancelled':
            # Refund buyer's credits if order is cancelled
            buyer_profile, _ = UserProfile.objects.get_or_create(
                user=order.buyer,
                defaults={'virtual_credits': 5000.00}
            )
            buyer_profile.virtual_credits += order.price
            buyer_profile.save()
            Transaction.objects.create(
                user=order.buyer,
                transaction_type='refund',
                amount=order.price,
                balance_after=buyer_profile.virtual_credits,
                description=f"Refund for cancelled Order #{order.id}: {order.gig.title}",
                order=order
            )
        order.save()
        
        # Create notification
        from .models import Notification
        notification_messages = {
            'in_progress': f"Your order for {order.gig.title} has been accepted and is now in progress",
            'delivered': f"Your order for {order.gig.title} has been delivered. Please review and complete.",
            'completed': f"Your order for {order.gig.title} has been completed. Thank you!",
            'cancelled': f"Your order for {order.gig.title} has been cancelled"
        }
        
        notification_types = {
            'in_progress': 'order_accepted',
            'delivered': 'order_delivered',
            'completed': 'order_completed',
            'cancelled': 'order_cancelled'
        }
        
        # Send notification to the appropriate user
        if new_status in notification_types:
            # For completion, notify seller; for others, notify buyer
            recipient = order.seller if new_status == 'completed' else order.buyer
            Notification.objects.create(
                user=recipient,
                notification_type=notification_types[new_status],
                title=f"Order {new_status.replace('_', ' ').title()}",
                message=notification_messages[new_status],
                order=order
            )
        
        return JsonResponse({
            'success': True,
            'status': order.status,
            'message': f'Order status updated to {order.get_status_display()}'
        })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def order_detail(request, order_id):
    """View order details and messages"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user is buyer or seller
    if request.user != order.buyer and request.user != order.seller:
        messages.error(request, 'You do not have permission to view this order')
        return redirect('dashboard')
    
    # Mark messages as read
    Message.objects.filter(order=order).exclude(sender=request.user).update(is_read=True)
    
    order_messages = order.messages.all()
    
    return render(request, 'marketplace/order_detail.html', {
        'order': order,
        'order_messages': order_messages
    })

@login_required
@require_http_methods(["POST"])
def send_message_json(request, order_id):
    """Send a message for an order (backward compatible)"""
    return send_chat_message_json(request, order_id=order_id)

@login_required
@require_http_methods(["POST"])
def send_chat_message_json(request, order_id=None):
    """
    WhatsApp Messenger send message endpoint:
    Supports text, image, and document file attachments.
    """
    try:
        message_text = ''
        target_username = None
        target_order_id = order_id
        
        # Check if multipart form or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            message_text = request.POST.get('message', '').strip()
            target_username = request.POST.get('username', '').strip() or None
            if not target_order_id and request.POST.get('order_id'):
                target_order_id = int(request.POST.get('order_id'))
        else:
            try:
                data = json.loads(request.body)
                message_text = data.get('message', '').strip()
                target_username = data.get('username', '').strip() or None
                if not target_order_id and data.get('order_id'):
                    target_order_id = int(data.get('order_id'))
            except Exception:
                pass
        
        attachment = request.FILES.get('attachment')
        if not message_text and not attachment:
            return JsonResponse({'success': False, 'error': 'Please enter a message or select an attachment'}, status=400)
            
        attachment_name = None
        attachment_type = None
        if attachment:
            attachment_name = attachment.name
            ext = os.path.splitext(attachment.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                attachment_type = 'image'
            else:
                attachment_type = 'document'
                
        order = None
        recipient = None
        
        if target_order_id:
            order = get_object_or_404(Order, id=target_order_id)
            if request.user != order.buyer and request.user != order.seller:
                return JsonResponse({'success': False, 'error': 'You do not have permission to message this order'}, status=403)
            recipient = order.seller if request.user == order.buyer else order.buyer
        elif target_username:
            recipient = get_object_or_404(User, username=target_username)
            if recipient == request.user:
                return JsonResponse({'success': False, 'error': 'Cannot send messages to yourself'}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Target order or username required'}, status=400)
            
        msg = Message.objects.create(
            order=order,
            sender=request.user,
            recipient=recipient,
            message=message_text,
            attachment=attachment,
            attachment_name=attachment_name,
            attachment_type=attachment_type
        )
        
        # Notify recipient
        notif_msg = message_text[:80] if message_text else f"Sent an attachment ({attachment_name})"
        Notification.objects.create(
            user=recipient,
            notification_type='message_received',
            title=f"New message from {request.user.username}",
            message=notif_msg,
            order=order
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': msg.id,
                'sender': msg.sender.username,
                'sender_avatar': msg.sender.username[0].upper(),
                'message': msg.message,
                'has_attachment': bool(msg.attachment),
                'attachment_url': msg.attachment.url if msg.attachment else None,
                'attachment_name': msg.attachment_name,
                'attachment_type': msg.attachment_type,
                'created_at': msg.created_at.isoformat(),
                'time_formatted': msg.created_at.strftime('%I:%M %p'),
                'is_own': True,
                'is_read': False
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def get_notifications_json(request):
    """Get all notifications for the current user (optimized batch query)"""
    from .models import Notification
    
    notifications = list(Notification.objects.filter(user=request.user).select_related('order')[:20])
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'type': notif.notification_type,
            'title': notif.title,
            'message': notif.message,
            'is_read': notif.is_read,
            'created_at': notif.created_at.isoformat(),
            'order_id': notif.order.id if notif.order else None
        })
    
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count
    })

@login_required
def mark_notification_read_json(request, notification_id):
    """Mark a notification as read"""
    from .models import Notification
    
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)

@login_required
def mark_all_notifications_read_json(request):
    """Mark all notifications as read"""
    from .models import Notification
    
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    return JsonResponse({'success': True})

@login_required
def get_conversations_json(request):
    """
    Get unique WhatsApp-style conversations grouped by contact (person).
    Each person appears EXACTLY ONCE in the list.
    Optimized to run in O(1) batch queries instead of O(N) per-contact loops.
    """
    from django.db.models import Q, Count

    # 1. Collect all distinct contacts from both direct messages and orders
    message_user_ids = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).values_list('sender_id', 'recipient_id')

    related_user_ids = set()
    for s_id, r_id in message_user_ids:
        if s_id and s_id != request.user.id:
            related_user_ids.add(s_id)
        if r_id and r_id != request.user.id:
            related_user_ids.add(r_id)

    order_user_ids = Order.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).values_list('buyer_id', 'seller_id')
    for b_id, s_id in order_user_ids:
        if b_id and b_id != request.user.id:
            related_user_ids.add(b_id)
        if s_id and s_id != request.user.id:
            related_user_ids.add(s_id)

    conversations = []

    if related_user_ids:
        # Pre-fetch all relevant users in 1 batch query
        users_by_id = {u.id: u for u in User.objects.filter(id__in=related_user_ids)}

        # Pre-fetch unread counts for all contacts in 1 batch query
        unread_counts_qs = Message.objects.filter(
            recipient=request.user,
            sender_id__in=related_user_ids,
            is_read=False
        ).values('sender_id').annotate(count=Count('id'))
        unread_map = {item['sender_id']: item['count'] for item in unread_counts_qs}

        # Pre-fetch latest order for each contact in 1 batch query
        all_orders = Order.objects.filter(
            (Q(buyer=request.user, seller_id__in=related_user_ids) | Q(seller=request.user, buyer_id__in=related_user_ids))
        ).select_related('gig').order_by('-created_at')
        latest_order_map = {}
        for ord_item in all_orders:
            other_id = ord_item.seller_id if ord_item.buyer_id == request.user.id else ord_item.buyer_id
            if other_id not in latest_order_map:
                latest_order_map[other_id] = ord_item

        # Pre-fetch latest message for each contact in 1 batch query
        all_msgs = Message.objects.filter(
            (Q(sender=request.user, recipient_id__in=related_user_ids) | Q(sender_id__in=related_user_ids, recipient=request.user)) |
            (Q(order__buyer=request.user, order__seller_id__in=related_user_ids) | Q(order__seller=request.user, order__buyer_id__in=related_user_ids))
        ).select_related('order').order_by('created_at')

        last_msg_map = {}
        for m in all_msgs:
            if m.sender_id == request.user.id:
                other_id = m.recipient_id or (m.order.seller_id if (m.order and m.order.buyer_id == request.user.id) else (m.order.buyer_id if m.order else None))
            else:
                other_id = m.sender_id
            if other_id and other_id in related_user_ids:
                last_msg_map[other_id] = m

        now_iso = timezone.now().isoformat()
        for other_user_id in related_user_ids:
            other_user = users_by_id.get(other_user_id)
            if not other_user:
                continue

            last_msg = last_msg_map.get(other_user_id)
            unread_count = unread_map.get(other_user_id, 0)
            latest_order = latest_order_map.get(other_user_id)

            last_text = "No messages yet"
            last_time = now_iso
            has_attachment = False

            if last_msg:
                last_time = last_msg.created_at.isoformat()
                if last_msg.message:
                    last_text = (last_msg.message[:45] + '...') if len(last_msg.message) > 45 else last_msg.message
                elif last_msg.attachment:
                    last_text = "📎 " + (last_msg.attachment_name or "Attachment")
                    has_attachment = True
            elif latest_order:
                last_time = latest_order.created_at.isoformat()
                last_text = f"Order #{latest_order.id} placed"

            order_title = latest_order.gig.title if (latest_order and latest_order.gig) else (f"Order #{latest_order.id}" if latest_order else None)

            conversations.append({
                'chat_id': f"user_{other_user.username}",
                'other_user': other_user.username,
                'other_user_avatar': other_user.username[0].upper(),
                'other_user_name': other_user.get_full_name() or other_user.username,
                'latest_order_id': latest_order.id if latest_order else None,
                'latest_order_title': order_title,
                'has_order': bool(latest_order),
                'status': 'Online',
                'last_message': last_text,
                'last_message_time': last_time,
                'has_attachment': has_attachment,
                'unread_count': unread_count
            })

    # If no conversations yet, add top creators as suggestions
    if len(conversations) == 0:
        top_sellers = User.objects.filter(gigs__status='active').exclude(id=request.user.id).distinct().prefetch_related('gigs')[:4]
        for s in top_sellers:
            gig = s.gigs.filter(status='active').first()
            conversations.append({
                'chat_id': f"user_{s.username}",
                'other_user': s.username,
                'other_user_avatar': s.username[0].upper(),
                'other_user_name': s.get_full_name() or s.username,
                'latest_order_id': None,
                'latest_order_title': gig.title if gig else 'Top Specialist',
                'has_order': False,
                'status': 'Online',
                'last_message': 'Click to start chatting',
                'last_message_time': timezone.now().isoformat(),
                'has_attachment': False,
                'unread_count': 0
            })

    # Sort conversations by last_message_time descending
    conversations.sort(key=lambda c: c['last_message_time'], reverse=True)
    total_unread = sum(c['unread_count'] for c in conversations)

    return JsonResponse({
        'conversations': conversations,
        'total_unread': total_unread
    })


@login_required
def get_chat_messages_json(request):
    """
    Get messages for a conversation between the current user and the target contact.
    Guarantees that messages sent to User A never show in User B's thread.
    Optimized with select_related to prevent N+1 queries.
    """
    from django.db.models import Q

    username = request.GET.get('username')
    order_id = request.GET.get('order_id')

    other_user = None
    order_info = None

    if username:
        other_user = get_object_or_404(User, username=username)
    elif order_id and order_id != 'null':
        order = get_object_or_404(Order.objects.select_related('buyer', 'seller', 'gig'), id=int(order_id))
        if request.user != order.buyer and request.user != order.seller:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        other_user = order.seller if request.user == order.buyer else order.buyer
        order_info = {
            'id': order.id,
            'gig_title': order.gig.title if order.gig else f"Order #{order.id}",
            'price': float(order.price),
            'status': order.status
        }
    else:
        return JsonResponse({'success': False, 'error': 'Username or order_id required'}, status=400)

    if not order_info:
        # Find latest order between these two users if any
        latest_order = Order.objects.filter(
            (Q(buyer=request.user, seller=other_user) | Q(buyer=other_user, seller=request.user))
        ).select_related('gig').order_by('-created_at').first()
        if latest_order:
            order_info = {
                'id': latest_order.id,
                'gig_title': latest_order.gig.title if latest_order.gig else f"Order #{latest_order.id}",
                'price': float(latest_order.price),
                'status': latest_order.status
            }

    # Query strictly messages between request.user and other_user with select_related
    messages_qs = Message.objects.filter(
        (Q(sender=request.user, recipient=other_user) | Q(sender=other_user, recipient=request.user)) |
        (Q(order__buyer=request.user, order__seller=other_user) | Q(order__buyer=other_user, order__seller=request.user))
    ).select_related('sender').distinct().order_by('created_at')

    # Mark incoming unread messages from this contact as read efficiently
    Message.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    messages_data = []
    for msg in messages_qs:
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'sender_avatar': msg.sender.username[0].upper(),
            'message': msg.message,
            'has_attachment': bool(msg.attachment),
            'attachment_url': msg.attachment.url if msg.attachment else None,
            'attachment_name': msg.attachment_name,
            'attachment_type': msg.attachment_type,
            'created_at': msg.created_at.isoformat(),
            'time_formatted': msg.created_at.strftime('%I:%M %p'),
            'date_formatted': msg.created_at.strftime('%b %d, %Y'),
            'is_own': msg.sender == request.user,
            'is_read': msg.is_read
        })

    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'other_user': {
            'username': other_user.username,
            'avatar': other_user.username[0].upper(),
            'name': other_user.get_full_name() or other_user.username,
            'status': 'Online'
        },
        'order_info': order_info
    })



@login_required
def get_order_messages_json(request, order_id):
    """Legacy endpoint wrapper for order messages"""
    request.GET = request.GET.copy()
    request.GET['order_id'] = str(order_id)
    return get_chat_messages_json(request)


@login_required
def get_chat_contacts_json(request):
    """
    Get list of potential contacts (active sellers/creators) for starting a new chat.
    Optimized to run in 1 single query instead of N queries per seller.
    """
    gigs = Gig.objects.filter(
        status='active'
    ).exclude(seller=request.user).select_related('seller', 'category')
    
    seen_sellers = set()
    contacts = []
    for gig in gigs:
        seller = gig.seller
        if seller.id not in seen_sellers:
            seen_sellers.add(seller.id)
            contacts.append({
                'username': seller.username,
                'avatar': seller.username[0].upper(),
                'specialty': gig.category.name if gig.category else 'Specialist',
                'gig_title': gig.title
            })
            if len(contacts) >= 20:
                break
        
    return JsonResponse({'contacts': contacts})


def get_categories_json(request):
    """
    API endpoint: Get all categories
    URL: /api/categories/
    """
    categories = Category.objects.all()
    
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'icon': category.icon,
        })
    
    return JsonResponse({'categories': categories_data})


@login_required
def get_seller_earnings_json(request):
    """
    API endpoint: Get seller's earnings breakdown
    URL: /api/seller/earnings/
    """
    # Get all completed orders where user is seller
    completed_orders = Order.objects.filter(
        seller=request.user, 
        status='completed'
    ).select_related('gig', 'buyer')
    
    total_earnings = 0
    earnings_by_gig = {}
    recent_earnings = []
    
    for order in completed_orders:
        total_earnings += float(order.price)
        
        # Group by gig
        gig_title = order.gig.title
        if gig_title not in earnings_by_gig:
            earnings_by_gig[gig_title] = {
                'gig_title': gig_title,
                'orders_count': 0,
                'total_earned': 0
            }
        
        earnings_by_gig[gig_title]['orders_count'] += 1
        earnings_by_gig[gig_title]['total_earned'] += float(order.price)
        
        # Recent earnings (last 10)
        recent_earnings.append({
            'order_id': order.id,
            'gig_title': order.gig.title,
            'amount': float(order.price),
            'buyer': order.buyer.username,
            'completed_at': order.updated_at.strftime('%b %d, %Y')
        })
    
    # Sort recent earnings by date (most recent first)
    recent_earnings = sorted(recent_earnings, key=lambda x: x['order_id'], reverse=True)[:10]
    
    # Calculate available earnings after approved cashouts
    from django.db.models import Sum
    total_cashed_out = CashoutRequest.objects.filter(
        user=request.user,
        status='approved'
    ).aggregate(total=Sum('amount'))['total'] or 0
    available_earnings = float(total_earnings) - float(total_cashed_out)

    return JsonResponse({
        'total_earnings': float(total_earnings),
        'available_earnings': available_earnings,
        'total_orders': len(completed_orders),
        'earnings_by_gig': list(earnings_by_gig.values()),
        'recent_earnings': recent_earnings
    })


@login_required
@require_http_methods(["POST"])
def request_balance(request):
    """Create a balance request"""
    try:
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))
        note = data.get('note', '').strip()
        
        if amount <= 0:
            return JsonResponse({'error': 'Amount must be greater than 0'}, status=400)
        
        # Create balance request
        balance_request = BalanceRequest.objects.create(
            user=request.user,
            amount=amount,
            note=note,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Balance request submitted successfully',
            'request_id': balance_request.id
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_balance_requests(request):
    """Get user's balance requests"""
    requests_list = BalanceRequest.objects.filter(user=request.user).order_by('-created_at')
    
    data = []
    for req in requests_list:
        data.append({
            'id': req.id,
            'amount': float(req.amount),
            'status': req.status,
            'note': req.note,
            'admin_note': req.admin_note,
            'created_at': req.created_at.strftime('%b %d, %Y %I:%M %p'),
            'updated_at': req.updated_at.strftime('%b %d, %Y %I:%M %p')
        })
    
    return JsonResponse({'requests': data})


@login_required
@require_http_methods(["POST"])
def request_cashout(request):
    """Create a cashout request"""
    try:
        from django.db.models import Sum
        
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))
        payment_method = data.get('payment_method', '').strip()
        payment_details = data.get('payment_details', '').strip()
        note = data.get('note', '').strip()
        
        if amount <= 0:
            return JsonResponse({'error': 'Amount must be greater than 0'}, status=400)
        
        if not payment_method or not payment_details:
            return JsonResponse({'error': 'Payment method and details are required'}, status=400)
        
        # Calculate available earnings
        total_earnings = Order.objects.filter(
            seller=request.user,
            status='completed'
        ).aggregate(total=Sum('price'))['total'] or 0
        
        # Get total already cashed out
        total_cashed_out = CashoutRequest.objects.filter(
            user=request.user,
            status='approved'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        available_earnings = float(total_earnings) - float(total_cashed_out)
        
        if amount > available_earnings:
            return JsonResponse({
                'error': f'Insufficient earnings. Available: {available_earnings:.2f} Taka'
            }, status=400)
        
        # Create cashout request
        cashout_request = CashoutRequest.objects.create(
            user=request.user,
            amount=amount,
            payment_method=payment_method,
            payment_details=payment_details,
            note=note,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Cashout request submitted successfully',
            'request_id': cashout_request.id,
            'available_earnings': available_earnings - amount
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_cashout_requests(request):
    """Get user's cashout requests"""
    requests_list = CashoutRequest.objects.filter(user=request.user).order_by('-created_at')
    
    data = []
    for req in requests_list:
        data.append({
            'id': req.id,
            'amount': float(req.amount),
            'status': req.status,
            'payment_method': req.payment_method,
            'payment_details': req.payment_details,
            'note': req.note,
            'admin_note': req.admin_note,
            'created_at': req.created_at.strftime('%b %d, %Y %I:%M %p'),
            'updated_at': req.updated_at.strftime('%b %d, %Y %I:%M %p')
        })
    
    return JsonResponse({'requests': data})


@login_required
def get_available_earnings(request):
    """Get user's available earnings for cashout"""
    from django.db.models import Sum
    
    # Calculate total earnings
    total_earnings = Order.objects.filter(
        seller=request.user,
        status='completed'
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Get total already cashed out
    total_cashed_out = CashoutRequest.objects.filter(
        user=request.user,
        status='approved'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    available_earnings = float(total_earnings) - float(total_cashed_out)
    
    return JsonResponse({
        'total_earnings': float(total_earnings),
        'total_cashed_out': float(total_cashed_out),
        'available_earnings': available_earnings
    })

@login_required
@require_http_methods(["POST"])
def generate_text_content(request):
    """Generate marketing content - currently unavailable due to AI API maintenance"""
    return JsonResponse({
        'success': False,
        'error': 'AI text generation service is temporarily unavailable as the AI API is undergoing maintenance. Please check back soon.'
    }, status=503)

@login_required
@require_http_methods(["POST"])
def generate_product_image(request):
    """Generate product image - currently unavailable due to AI API maintenance"""
    return JsonResponse({
        'success': False,
        'error': 'AI image generation service is temporarily unavailable as the AI API is undergoing maintenance. Please check back soon.'
    }, status=503)
