from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Gig, Order, UserProfile, Category, Transaction, Message, BalanceRequest, CashoutRequest
import json
import os
import requests
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
from django.core.files.base import ContentFile
from openai import OpenAI

def home(request):
    """Render the home page (HTML skeleton)"""
    return render(request, 'marketplace/home.html')

def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'marketplace/login.html')

def logout_view(request):
    """Handle user logout"""
    auth_logout(request)
    return redirect('home')

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user, virtual_credits=5000.00)
            auth_login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    
    return render(request, 'marketplace/register.html')

def gig_detail(request, gig_id):
    """Render the gig detail page"""
    return render(request, 'marketplace/gig_detail.html')

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
                    auth_login(request, request.user)  # Re-login after password change
                    messages.success(request, 'Password updated successfully!')
                    return redirect('profile')
            
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
        buyer_profile = get_object_or_404(UserProfile, user=request.user)
        
        # Check if user has enough credits
        if buyer_profile.virtual_credits < gig.price:
            return JsonResponse({
                'success': False,
                'error': 'Insufficient Taka'
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
            
            # Add credits to seller
            seller_profile = get_object_or_404(UserProfile, user=gig.seller)
            seller_profile.virtual_credits += gig.price
            seller_profile.save()
            
            # Create order
            order = Order.objects.create(
                gig=gig,
                buyer=request.user,
                seller=gig.seller,
                price=gig.price,
                requirements=requirements,
                status='pending'
            )
            
            # Create transaction records
            Transaction.objects.create(
                user=request.user,
                transaction_type='debit',
                amount=gig.price,
                balance_after=buyer_profile.virtual_credits,
                description=f"Purchase: {gig.title}",
                order=order
            )
            
            Transaction.objects.create(
                user=gig.seller,
                transaction_type='earning',
                amount=gig.price,
                balance_after=seller_profile.virtual_credits,
                description=f"Sale: {gig.title}",
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
def get_user_balance_json(request):
    """
    API endpoint: Get current user's virtual credit balance
    URL: /api/user/balance/
    """
    profile = get_object_or_404(UserProfile, user=request.user)
    return JsonResponse({
        'balance': float(profile.virtual_credits),
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
    """Generate poster using AI"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        product_image = request.FILES.get('product_image')
        logo_image = request.FILES.get('logo_image')
        description = request.POST.get('description', '')
        
        if not product_image or not description:
            return JsonResponse({'success': False, 'error': 'Product image and description are required'}, status=400)
        
        # Configure Gemini API for caption generation
        gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not gemini_key:
            return JsonResponse({'success': False, 'error': 'API key not configured'}, status=500)
        
        # Step 1: Generate AI caption using Gemini
        caption_prompt = f"""Create a catchy, engaging social media caption for a poster with this description: {description}
        
        Requirements:
        - Make it short and punchy (2-3 sentences max)
        - Include relevant emojis
        - Add 3-5 relevant hashtags at the end
        - Make it shareable and attention-grabbing
        - Focus on benefits and call-to-action"""
        
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {gemini_key}',
                    'HTTP-Referer': 'https://adezy.com',
                    'X-Title': 'AdEzy AI Generator',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'google/gemini-2.0-flash-exp:free',
                    'messages': [{'role': 'user', 'content': caption_prompt}]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_caption = result['choices'][0]['message']['content']
            else:
                ai_caption = "Check out this amazing product! 🌟 #ad #product #amazing"
        except Exception as e:
            print(f"Caption generation error: {e}")
            ai_caption = "Check out this amazing product! 🌟 #ad #product #amazing"
        
        # Step 2: Generate poster image using Seedream
        api_key = getattr(settings, 'SEEDREAM_API_KEY', None)
        
        # Read and encode the product image
        product_image.seek(0)
        product_image_data = product_image.read()
        
        # Build the poster generation prompt
        poster_prompt = f"""Create a professional, eye-catching social media poster (1080x1080px square format) with the following specifications:

Description: {description}

Design Requirements:
- Modern and clean design with gradient backgrounds
- Feature the product prominently in the center
- Add decorative elements like shapes, lines, or patterns
- Use bold, readable typography for any text
- Include empty space for text overlays
- Professional color scheme that matches the product
- High quality, print-ready design
- Instagram/Facebook ready format"""
        
        # Prepare the content for image generation
        if logo_image:
            logo_image.seek(0)
            logo_image_data = logo_image.read()
            
            # Include both product and logo in generation
            generation_parts = [
                poster_prompt,
                {"mime_type": product_image.content_type, "data": product_image_data},
                "Include this logo in the top corner:",
                {"mime_type": logo_image.content_type, "data": logo_image_data}
            ]
        else:
            # Only product image
            generation_parts = [
                poster_prompt,
                {"mime_type": product_image.content_type, "data": product_image_data}
            ]
        
        # Generate the poster using Seedream
        # For image generation with Seedream, we'll use a different approach
        # Since Seedream primarily focuses on text generation, we'll create enhanced prompts
        image_response = None  # Placeholder for now
        
        # Extract generated image from response
        # The response typically contains base64 encoded image data
        generated_image_data = None
        
        if hasattr(image_response, 'parts'):
            for part in image_response.parts:
                if hasattr(part, 'inline_data'):
                    generated_image_data = part.inline_data.data
                    break
        
        if not generated_image_data:
            # Fallback to PIL-based generation if AI generation fails
            poster = create_poster_image(product_image, logo_image, description)
            poster_filename = f'poster_{request.user.id}_{timezone.now().timestamp()}.jpg'
            poster_path = os.path.join(settings.MEDIA_ROOT, 'posters', poster_filename)
            os.makedirs(os.path.dirname(poster_path), exist_ok=True)
            poster.save(poster_path, 'JPEG', quality=95)
        else:
            # Save the AI-generated poster
            import base64
            poster_filename = f'poster_{request.user.id}_{timezone.now().timestamp()}.jpg'
            poster_path = os.path.join(settings.MEDIA_ROOT, 'posters', poster_filename)
            os.makedirs(os.path.dirname(poster_path), exist_ok=True)
            
            # Decode and save the image
            with open(poster_path, 'wb') as f:
                f.write(base64.b64decode(generated_image_data))
        
        poster_url = os.path.join(settings.MEDIA_URL, 'posters', poster_filename)
        
        return JsonResponse({
            'success': True,
            'poster_url': poster_url,
            'description': ai_caption
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating poster: {error_details}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
    """Send a message for an order"""
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        order = get_object_or_404(Order, id=order_id)
        
        # Check if user is buyer or seller
        if request.user != order.buyer and request.user != order.seller:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to message this order'
            }, status=403)
        
        message = Message.objects.create(
            order=order,
            sender=request.user,
            message=message_text
        )
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'sender': request.user.username,
            'message': message.message,
            'created_at': message.created_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def get_notifications_json(request):
    """Get all notifications for the current user"""
    from .models import Notification
    
    notifications = Notification.objects.filter(user=request.user)[:20]
    
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
    """Get all conversations (orders with messages) for the current user"""
    from django.db.models import Q, Count, Max
    
    # Get orders where user is buyer or seller and has messages
    orders = Order.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).annotate(
        message_count=Count('messages'),
        last_message_time=Max('messages__created_at')
    ).filter(message_count__gt=0).order_by('-last_message_time')
    
    conversations = []
    for order in orders:
        # Get last message
        last_message = order.messages.last()
        
        # Count unread messages
        unread_count = order.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()
        
        # Determine the other party
        other_user = order.seller if request.user == order.buyer else order.buyer
        
        conversations.append({
            'order_id': order.id,
            'gig_title': order.gig.title if order.gig else 'Order #' + str(order.id),
            'other_user': other_user.username,
            'last_message': last_message.message[:50] + ('...' if len(last_message.message) > 50 else ''),
            'last_message_time': last_message.created_at.isoformat(),
            'unread_count': unread_count,
            'status': order.status
        })
    
    return JsonResponse({
        'conversations': conversations,
        'total_unread': sum(c['unread_count'] for c in conversations)
    })

@login_required
def get_order_messages_json(request, order_id):
    """Get all messages for an order"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user is buyer or seller
    if request.user != order.buyer and request.user != order.seller:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to view these messages'
        }, status=403)
    
    # Mark messages as read
    order.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    messages_data = []
    for msg in order.messages.all():
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'message': msg.message,
            'created_at': msg.created_at.isoformat(),
            'is_own': msg.sender == request.user
        })
    
    # Get order details
    other_user = order.seller if request.user == order.buyer else order.buyer
    
    return JsonResponse({
        'messages': messages_data,
        'order_info': {
            'id': order.id,
            'gig_title': order.gig.title if order.gig else 'Order #' + str(order.id),
            'other_user': other_user.username,
            'status': order.status,
            'price': float(order.price)
        }
    })


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
    ).select_related('gig')
    
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
    
    return JsonResponse({
        'total_earnings': total_earnings,
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
    """Generate marketing content (captions, hashtags, etc.) using AI"""
    try:
        data = json.loads(request.body)
        product_desc = data.get('product_desc', '').strip()
        target_audience = data.get('target_audience', '').strip()
        platform = data.get('platform', 'general')
        
        gen_caption = data.get('gen_caption', False)
        gen_hashtags = data.get('gen_hashtags', False)
        gen_cta = data.get('gen_cta', False)
        gen_hooks = data.get('gen_hooks', False)
        
        if not product_desc:
            return JsonResponse({'success': False, 'error': 'Product description is required'}, status=400)
        
        # Configure Gemini API for text generation
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return JsonResponse({'success': False, 'error': 'API key not configured'}, status=500)
        
        content = {}
        
        # Generate Caption
        if gen_caption:
            caption_prompt = f"""Create an engaging social media caption for {platform} with these details:
Product: {product_desc}
Target Audience: {target_audience or 'general audience'}

Requirements:
- Make it catchy and attention-grabbing
- 2-3 sentences max
- Include relevant emojis naturally
- Focus on benefits and emotional appeal
- Platform-appropriate tone for {platform}
- End with a subtle call-to-action

Return only the caption, nothing else."""
            
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'HTTP-Referer': 'https://adezy.com',
                    'X-Title': 'AdEzy AI Generator',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'google/gemini-2.0-flash-exp:free',
                    'messages': [{'role': 'user', 'content': caption_prompt}]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content['caption'] = result['choices'][0]['message']['content'].strip()
            else:
                print(f"Caption API Error: {response.status_code}, {response.text}")
                content['caption'] = "Unable to generate caption at this time."
        
        # Generate Hashtags
        if gen_hashtags:
            hashtags_prompt = f"""Generate relevant hashtags for this product on {platform}:
Product: {product_desc}
Target Audience: {target_audience or 'general audience'}

Requirements:
- Mix of popular and niche hashtags
- 10-15 hashtags
- Include branded, category, and trending hashtags
- Platform-appropriate for {platform}
- Format: #hashtag1 #hashtag2 #hashtag3 etc.

Return only the hashtags separated by spaces, nothing else."""
            
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'HTTP-Referer': 'https://adezy.com',
                    'X-Title': 'AdEzy AI Generator',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'google/gemini-2.0-flash-exp:free',
                    'messages': [{'role': 'user', 'content': hashtags_prompt}]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content['hashtags'] = result['choices'][0]['message']['content'].strip()
            else:
                print(f"Hashtags API Error: {response.status_code}, {response.text}")
                content['hashtags'] = "#marketing #business #product"
        
        # Generate Call to Action
        if gen_cta:
            cta_prompt = f"""Create 3 powerful call-to-action lines for {platform} promoting:
Product: {product_desc}
Target Audience: {target_audience or 'general audience'}

Requirements:
- Action-oriented and urgent
- One line each (separate with line breaks)
- Include emojis
- Create FOMO (fear of missing out)
- Platform-appropriate for {platform}

Return only the 3 CTA lines, nothing else."""
            
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'HTTP-Referer': 'https://adezy.com',
                    'X-Title': 'AdEzy AI Generator',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'google/gemini-2.0-flash-exp:free',
                    'messages': [{'role': 'user', 'content': cta_prompt}]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content['cta'] = result['choices'][0]['message']['content'].strip()
            else:
                print(f"CTA API Error: {response.status_code}, {response.text}")
                content['cta'] = "🔥 Get yours now!\n💥 Limited time offer!\n✨ Don't miss out!"
        
        # Generate Hook Lines
        if gen_hooks:
            hooks_prompt = f"""Create 5 attention-grabbing hook lines to start a {platform} post about:
Product: {product_desc}
Target Audience: {target_audience or 'general audience'}

Requirements:
- Make people stop scrolling
- Question-based or surprising statements
- One line each (separate with line breaks)
- Include emojis where appropriate
- Curiosity-driven

Return only the 5 hook lines, nothing else."""
            
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'HTTP-Referer': 'https://adezy.com',
                    'X-Title': 'AdEzy AI Generator',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'google/gemini-2.0-flash-exp:free',
                    'messages': [{'role': 'user', 'content': hooks_prompt}]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content['hooks'] = result['choices'][0]['message']['content'].strip()
            else:
                print(f"Hooks API Error: {response.status_code}, {response.text}")
                content['hooks'] = "🤔 Want to know a secret?\n💡 What if I told you...\n🎯 Ready to transform your life?\n⚡ This changes everything!\n🌟 You won't believe this!"
        
        return JsonResponse({
            'success': True,
            'content': content
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating text content: {error_details}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def generate_product_image(request):
    """Generate product image using AI"""
    try:
        import requests
        import base64
        from io import BytesIO
        
        data = json.loads(request.body)
        product_type = data.get('product_type', '').strip()
        style = data.get('style', '').strip()
        background = data.get('background', 'white')
        format_type = data.get('format', 'square')
        
        if not product_type or not style:
            return JsonResponse({'success': False, 'error': 'Product type and style are required'}, status=400)
        
        # Map format to dimensions
        format_map = {
            'square': (1080, 1080),
            'portrait': (1080, 1350),
            'story': (1080, 1920),
            'landscape': (1200, 628)
        }
        width, height = format_map.get(format_type, (1080, 1080))
        
        # Map background to descriptive text
        background_map = {
            'white': 'clean white background, minimalist, professional, studio lighting',
            'gradient': 'modern gradient background (purple to blue), vibrant colors, eye-catching, dynamic',
            'wooden': 'rustic wooden table surface, natural wood grain texture, warm brown tones, soft natural light',
            'marble': 'luxury white marble surface with gray veins, elegant, high-end aesthetic, pristine',
            'lifestyle': 'realistic lifestyle setting, natural environment, authentic, in-context usage',
            'nature': 'outdoor natural setting, lush greenery, soft sunlight, organic atmosphere',
            'studio': 'professional photography studio, dramatic lighting, dark background, spotlight on subject'
        }
        background_desc = background_map.get(background, 'neutral background')
        
        # Configure Seedream API
        api_key = getattr(settings, 'SEEDREAM_API_KEY', None)
        if not api_key:
            return JsonResponse({'success': False, 'error': 'API key not configured'}, status=500)
        
        # Create highly detailed prompt for image generation
        detailed_prompt = f"""Create a high-quality, professional product photography image of: {product_type}

Style & Details: {style}

Background: {background_desc}

Technical specifications:
- Resolution: {width}x{height}px
- Ultra-high quality, 8K resolution
- Professional product photography
- Sharp focus on the product
- Perfect composition and framing
- Photorealistic rendering
- Professional color grading
- Studio-quality lighting

Composition guidelines:
- Center the product prominently
- Ensure the product takes up 60-70% of the frame
- Maintain proper proportions and perspective
- Add subtle shadows for depth
- Include soft highlights to show texture
- Professional product shot aesthetic

If text is mentioned in the prompt, render it with:
- Bold, sans-serif font (like Montserrat Bold or Impact)
- White text color (#FFFFFF)
- Thick black outline/stroke (3-4px) for contrast
- High readability and visibility
- Positioned according to composition rules
- Shadow effect for depth

Make the image look like a professional advertisement or social media post, ready to use immediately."""
        
        # Use OpenRouter with Seedream for image generation
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'HTTP-Referer': 'https://adezy.com',
                    'X-Title': 'AdEzy AI Generator',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'bytedance-seed/seedream-4.5',
                    'messages': [
                        {
                            'role': 'user',
                            'content': [
                                {
                                    'type': 'text',
                                    'text': detailed_prompt
                                }
                            ]
                        }
                    ],
                    'max_tokens': 1024,
                    'temperature': 0.7
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if image was generated
                if 'choices' in result and len(result['choices']) > 0:
                    message = result['choices'][0].get('message', {})
                    
                    # Look for image in the response
                    if 'content' in message:
                        content = message['content']
                        
                        # Check if content is a list (multimodal response)
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'image_url':
                                    image_url = item.get('image_url', {}).get('url', '')
                                    if image_url:
                                        # Download and save the image
                                        image_filename = f'ai_product_{request.user.id}_{timezone.now().timestamp()}.jpg'
                                        image_path = os.path.join(settings.MEDIA_ROOT, 'ai_images', image_filename)
                                        os.makedirs(os.path.dirname(image_path), exist_ok=True)
                                        
                                        # Handle base64 or URL
                                        if image_url.startswith('data:image'):
                                            # Base64 encoded image
                                            image_data = image_url.split('base64,')[1]
                                            with open(image_path, 'wb') as f:
                                                f.write(base64.b64decode(image_data))
                                        else:
                                            # URL - download the image
                                            img_response = requests.get(image_url)
                                            with open(image_path, 'wb') as f:
                                                f.write(img_response.content)
                                        
                                        final_image_url = os.path.join(settings.MEDIA_URL, 'ai_images', image_filename)
                                        return JsonResponse({
                                            'success': True,
                                            'image_url': final_image_url,
                                            'prompt_used': detailed_prompt
                                        })
            
            # If image generation via API didn't work, create enhanced placeholder
            print(f"Seedream response: {response.status_code}, {response.text}")
            
        except Exception as api_error:
            print(f"API Error: {api_error}")
        
        # Fallback: Create enhanced placeholder with PIL
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
        
        # Create high-quality base image
        img = Image.new('RGB', (width, height), color='#ffffff')
        draw = ImageDraw.Draw(img)
        
        # Create sophisticated gradient background
        for i in range(height):
            alpha = i / height
            if background == 'gradient':
                # Purple to blue gradient
                r = int(147 * (1 - alpha) + 59 * alpha)
                g = int(51 * (1 - alpha) + 130 * alpha)
                b = int(234 * (1 - alpha) + 246 * alpha)
            elif background == 'wooden':
                # Warm brown tones
                r = int(139 * (1 - alpha) + 101 * alpha)
                g = int(90 * (1 - alpha) + 67 * alpha)
                b = int(43 * (1 - alpha) + 33 * alpha)
            elif background == 'marble':
                # White with subtle gray
                r = int(255 * (1 - alpha * 0.05))
                g = int(255 * (1 - alpha * 0.05))
                b = int(255 * (1 - alpha * 0.08))
            else:
                # Clean white to light gray
                r = g = b = int(255 * (1 - alpha * 0.02))
            draw.rectangle([(0, i), (width, i+1)], fill=(r, g, b))
        
        # Add decorative elements
        if background == 'gradient':
            # Add some circles for visual interest
            for _ in range(3):
                import random
                cx = random.randint(0, width)
                cy = random.randint(0, height)
                radius = random.randint(50, 150)
                draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], 
                           fill=(255, 255, 255, 30))
        
        # Load or create fonts
        try:
            # Try to load Impact font for bold text
            title_font = ImageFont.truetype("impact.ttf", int(height * 0.12))
            subtitle_font = ImageFont.truetype("arial.ttf", int(height * 0.05))
            small_font = ImageFont.truetype("arial.ttf", int(height * 0.03))
        except:
            try:
                title_font = ImageFont.truetype("arial.ttf", int(height * 0.12))
                subtitle_font = ImageFont.truetype("arial.ttf", int(height * 0.05))
                small_font = ImageFont.truetype("arial.ttf", int(height * 0.03))
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
        
        # Extract text from product description if mentioned
        main_text = product_type.upper()
        
        # Draw text with white fill and black outline
        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), main_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2 - int(height * 0.1)
        
        # Draw black outline (multiple passes for thick stroke)
        outline_width = 4
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text((x + offset_x, y + offset_y), main_text, 
                            fill='#000000', font=title_font)
        
        # Draw white text on top
        draw.text((x, y), main_text, fill='#FFFFFF', font=title_font)
        
        # Add style description below
        style_text = style[:50]
        bbox = draw.textbbox((0, 0), style_text, font=subtitle_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = y + text_height + int(height * 0.05)
        
        # Outline for subtitle
        for offset_x in range(-2, 3):
            for offset_y in range(-2, 3):
                if offset_x != 0 or offset_y != 0:
                    draw.text((x + offset_x, y + offset_y), style_text, 
                            fill='#000000', font=subtitle_font)
        draw.text((x, y), style_text, fill='#FFFFFF', font=subtitle_font)
        
        # Add watermark
        watermark = "AdEzy AI Studio"
        bbox = draw.textbbox((0, 0), watermark, font=small_font)
        text_width = bbox[2] - bbox[0]
        x = width - text_width - 20
        y = height - 40
        draw.text((x, y), watermark, fill=(255, 255, 255, 180), font=small_font)
        
        # Apply slight blur for professional look (subtle)
        # img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Enhance contrast and sharpness
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)
        
        # Save image
        image_filename = f'ai_product_{request.user.id}_{timezone.now().timestamp()}.jpg'
        image_path = os.path.join(settings.MEDIA_ROOT, 'ai_images', image_filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        img.save(image_path, 'JPEG', quality=95, optimize=True)
        
        image_url = os.path.join(settings.MEDIA_URL, 'ai_images', image_filename)
        
        return JsonResponse({
            'success': True,
            'image_url': image_url,
            'prompt_used': detailed_prompt
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating product image: {error_details}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
