"""
Custom admin site with separate session handling
"""
from django.contrib import admin
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import redirect
from django.urls import reverse


class SeparateSessionAdminSite(admin.AdminSite):
    """Admin site that uses separate session from main site"""
    
    site_header = 'AdEzy Administration'
    site_title = 'AdEzy Admin'
    index_title = 'Welcome to AdEzy Admin Panel'
    
    def has_permission(self, request):
        """Check if user has admin access using separate session"""
        admin_user_id = request.session.get('_admin_user_id')
        
        if admin_user_id:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(pk=admin_user_id)
                request.user = user  # Attach user to request
                return user.is_active and user.is_staff
            except User.DoesNotExist:
                pass
        
        return False
    
    def login(self, request, extra_context=None):
        """Handle admin login with separate session"""
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None and user.is_staff and user.is_active:
                # Store admin user ID in separate session key
                request.session['_admin_user_id'] = user.pk
                request.session['_admin_backend'] = 'django.contrib.auth.backends.ModelBackend'
                request.session.modified = True  # Force session save
                
                # Get the redirect URL
                redirect_url = request.GET.get('next', reverse('admin:index'))
                return redirect(redirect_url)
        
        return super().login(request, extra_context)
    
    def logout(self, request, extra_context=None):
        """Logout admin only - keep regular user session"""
        # Remove only admin session keys
        if '_admin_user_id' in request.session:
            del request.session['_admin_user_id']
        if '_admin_backend' in request.session:
            del request.session['_admin_backend']
        
        # Redirect to admin login
        return redirect(reverse('admin:login'))
    
    def each_context(self, request):
        """Get admin context for each request"""
        context = super().each_context(request)
        
        # Attach user from admin session
        admin_user_id = request.session.get('_admin_user_id')
        if admin_user_id:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(pk=admin_user_id)
                context['user'] = user
            except User.DoesNotExist:
                pass
        
        return context


# Create custom admin site instance
admin_site = SeparateSessionAdminSite(name='admin')
