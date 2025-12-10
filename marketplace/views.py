from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Gig, Order, UserProfile, Category, Transaction, Message
import json
import os
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
from django.core.files.base import ContentFile
import google.generativeai as genai

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
    API endpoint: Return all active gigs as JSON
    URL: /api/gigs/
    Note: Gigs remain available regardless of order status.
    Users can order the same gig multiple times.
    """
    gigs = Gig.objects.filter(status='active').select_related('seller', 'category')
    
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
        
        # Configure Gemini API
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return JsonResponse({'success': False, 'error': 'API key not configured'}, status=500)
        
        genai.configure(api_key=api_key)
        
        # Step 1: Generate AI caption using text model
        caption_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        caption_prompt = f"""Create a catchy, engaging social media caption for a poster with this description: {description}
        
        Requirements:
        - Make it short and punchy (2-3 sentences max)
        - Include relevant emojis
        - Add 3-5 relevant hashtags at the end
        - Make it shareable and attention-grabbing
        - Focus on benefits and call-to-action"""
        
        caption_response = caption_model.generate_content(caption_prompt)
        ai_caption = caption_response.text
        
        # Step 2: Generate poster image using Gemini Image model
        image_model = genai.GenerativeModel('gemini-2.5-flash-image')
        
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
        
        # Generate the poster
        image_response = image_model.generate_content(generation_parts)
        
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
