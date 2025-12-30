"""
Middleware to separate admin and regular user sessions
"""
from django.contrib.auth import login, logout
from django.contrib.auth.models import User, AnonymousUser


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
            # Handle regular user session - already loaded by AuthenticationMiddleware
            pass
        
        response = self.get_response(request)
        return response
    
    def _load_admin_session(self, request):
        """Load admin user from separate session key"""
        admin_user_id = request.session.get('_admin_user_id')
        
        if admin_user_id:
            try:
                user = User.objects.get(pk=admin_user_id)
                if user.is_active and user.is_staff:
                    # Override the request.user with admin user
                    request.user = user
                    request._cached_user = user
                else:
                    # Invalid admin session
                    if '_admin_user_id' in request.session:
                        del request.session['_admin_user_id']
                    request.user = AnonymousUser()
            except User.DoesNotExist:
                # User doesn't exist, clear session
                if '_admin_user_id' in request.session:
                    del request.session['_admin_user_id']
                request.user = AnonymousUser()
        else:
            # No admin session, ensure user is anonymous for admin area
            if not hasattr(request, 'user') or not request.user.is_staff:
                request.user = AnonymousUser()
    
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
