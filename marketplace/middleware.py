"""
Middleware to separate admin and regular user sessions
"""
from django.contrib.auth import login, logout
from django.contrib.auth.models import User


class SeparateAdminSessionMiddleware:
    """
    Middleware that maintains separate sessions for admin and regular users.
    Admin sessions are stored with a prefix to avoid conflicts.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is an admin request
        is_admin_request = request.path.startswith('/admin/')
        
        if is_admin_request:
            # Handle admin session
            self._load_admin_session(request)
        else:
            # Handle regular user session
            self._load_regular_session(request)
        
        response = self.get_response(request)
        
        # Save session state after response
        if is_admin_request:
            self._save_admin_session(request)
        else:
            self._save_regular_session(request)
        
        return response
    
    def _load_admin_session(self, request):
        """Load admin user from separate session key"""
        admin_user_id = request.session.get('_admin_user_id')
        
        if admin_user_id:
            try:
                user = User.objects.get(pk=admin_user_id)
                if user.is_active and user.is_staff:
                    request.user = user
                    request._cached_user = user
            except User.DoesNotExist:
                pass
    
    def _load_regular_session(self, request):
        """Regular session is handled by default Django auth"""
        pass
    
    def _save_admin_session(self, request):
        """Save admin session separately"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_staff:
                request.session['_admin_user_id'] = request.user.pk
        elif '_admin_user_id' in request.session:
            # Admin logged out
            del request.session['_admin_user_id']
    
    def _save_regular_session(self, request):
        """Regular session is handled by default Django auth"""
        pass
