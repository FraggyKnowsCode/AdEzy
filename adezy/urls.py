"""
URL configuration for adezy project.
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from marketplace.admin_site import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('marketplace.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
