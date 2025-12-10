from django.urls import path
from . import views

urlpatterns = [
    # Page routes (HTML skeletons)
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-gig/', views.create_gig, name='create-gig'),
    path('update-gig/<int:gig_id>/', views.update_gig, name='update-gig'),
    path('gig/<int:gig_id>/', views.gig_detail, name='gig-detail'),
    path('profile/', views.profile, name='profile'),
    path('imagine/', views.imagine_view, name='imagine'),
    path('order/<int:order_id>/', views.order_detail, name='order-detail'),
    path('css-showcase/', views.css_showcase, name='css-showcase'),
    
    # API routes (JSON endpoints)
    path('api/gigs/', views.get_all_gigs_json, name='api-gigs'),
    path('api/my-gigs/', views.get_my_gigs_json, name='api-my-gigs'),
    path('api/orders/<int:order_id>/status/', views.update_order_status_json, name='api-order-status'),
    path('api/notifications/', views.get_notifications_json, name='api-notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read_json, name='api-mark-notification-read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read_json, name='api-mark-all-notifications-read'),
    path('api/conversations/', views.get_conversations_json, name='api-conversations'),
    path('api/orders/<int:order_id>/messages/', views.get_order_messages_json, name='api-order-messages'),
    path('api/orders/<int:order_id>/send-message/', views.send_message_json, name='api-send-message'),
    path('api/gigs/<int:gig_id>/', views.get_gig_detail_json, name='api-gig-detail'),
    path('api/orders/create/', views.create_order_json, name='api-order-create'),
    path('api/orders/buyer/', views.get_buyer_orders_json, name='api-buyer-orders'),
    path('api/orders/seller/', views.get_seller_orders_json, name='api-seller-orders'),
    path('api/user/balance/', views.get_user_balance_json, name='api-user-balance'),
    path('api/categories/', views.get_categories_json, name='api-categories'),
    path('api/seller/earnings/', views.get_seller_earnings_json, name='api-seller-earnings'),
    path('api/generate-poster/', views.generate_poster_api, name='api-generate-poster'),
]
