from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserProfile, Category, Gig, Order, Review, Transaction, Message, BalanceRequest, CashoutRequest
from .admin_site import admin_site


@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Gig, site=admin_site)
class GigAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'category', 'price', 'status', 'created_at']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['title', 'seller__username']

@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'gig', 'buyer', 'seller', 'price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['buyer__username', 'seller__username', 'gig__title']

@admin.register(Review, site=admin_site)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'order', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['reviewer__username', 'comment']

@admin.register(Transaction, site=admin_site)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']

@admin.register(Message, site=admin_site)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['order', 'sender', 'message', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__username', 'message']


@admin.register(BalanceRequest, site=admin_site)
class BalanceRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'status', 'created_at', 'action_buttons']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'note', 'admin_note']
    readonly_fields = ['user', 'amount', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'amount', 'status', 'note')
        }),
        ('Admin Response', {
            'fields': ('admin_note', 'processed_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def action_buttons(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}">Approve</a> '
                '<a class="button" href="{}">Reject</a>',
                f'/admin/marketplace/balancerequest/{obj.id}/approve/',
                f'/admin/marketplace/balancerequest/{obj.id}/reject/'
            )
        return obj.status.upper()
    action_buttons.short_description = 'Actions'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:request_id>/approve/', self.admin_site.admin_view(self.approve_request), name='approve_balance_request'),
            path('<int:request_id>/reject/', self.admin_site.admin_view(self.reject_request), name='reject_balance_request'),
            path('manual-adjustment/', self.admin_site.admin_view(self.manual_adjustment), name='manual_balance_adjustment'),
        ]
        return custom_urls + urls
    
    def approve_request(self, request, request_id):
        balance_request = BalanceRequest.objects.get(id=request_id)
        
        if balance_request.status == 'pending':
            # Update user's virtual credits
            profile = balance_request.user.profile
            old_balance = profile.virtual_credits
            profile.virtual_credits += balance_request.amount
            profile.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=balance_request.user,
                transaction_type='credit',
                amount=balance_request.amount,
                balance_after=profile.virtual_credits,
                description=f'Balance request approved - Added {balance_request.amount} Taka'
            )
            
            # Update request status
            balance_request.status = 'approved'
            balance_request.processed_by = request.user
            balance_request.admin_note = f'Approved by {request.user.username}'
            balance_request.save()
            
            messages.success(request, f'Balance request approved! {balance_request.user.username}\'s balance updated from {old_balance} to {profile.virtual_credits} Taka')
        else:
            messages.error(request, 'This request has already been processed.')
        
        return redirect('admin:marketplace_balancerequest_changelist')
    
    def reject_request(self, request, request_id):
        balance_request = BalanceRequest.objects.get(id=request_id)
        
        if balance_request.status == 'pending':
            balance_request.status = 'rejected'
            balance_request.processed_by = request.user
            balance_request.admin_note = f'Rejected by {request.user.username}'
            balance_request.save()
            
            messages.warning(request, f'Balance request rejected for {balance_request.user.username}')
        else:
            messages.error(request, 'This request has already been processed.')
        
        return redirect('admin:marketplace_balancerequest_changelist')
    
    def manual_adjustment(self, request):
        if request.method == 'POST':
            from django.contrib.auth.models import User
            from decimal import Decimal
            
            user_id = request.POST.get('user_id')
            amount = Decimal(request.POST.get('amount'))
            adjustment_type = request.POST.get('adjustment_type')
            note = request.POST.get('note', '')
            
            user = User.objects.get(id=user_id)
            profile = user.profile
            old_balance = profile.virtual_credits
            
            if adjustment_type == 'add':
                profile.virtual_credits += amount
                transaction_type = 'credit'
                description = f'Manual balance addition by admin: {note}'
            else:  # subtract
                profile.virtual_credits -= amount
                transaction_type = 'debit'
                description = f'Manual balance deduction by admin: {note}'
            
            profile.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=user,
                transaction_type=transaction_type,
                amount=amount,
                balance_after=profile.virtual_credits,
                description=description
            )
            
            messages.success(request, f'{user.username}\'s balance updated from {old_balance} to {profile.virtual_credits} Taka')
            return redirect('admin:marketplace_userprofile_changelist')
        
        # GET request - show form
        from django.contrib.auth.models import User
        users = User.objects.all().order_by('username')
        context = {
            'title': 'Manual Balance Adjustment',
            'users': users,
        }
        return render(request, 'admin/manual_balance_adjustment.html', context)


@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'virtual_credits', 'is_seller_mode', 'created_at', 'balance_actions']
    list_filter = ['is_seller_mode', 'created_at']
    search_fields = ['user__username', 'user__email']
    
    def balance_actions(self, obj):
        return format_html(
            '<a class="button" href="/admin/marketplace/balancerequest/manual-adjustment/?user_id={}">Adjust Balance</a>',
            obj.user.id
        )
    balance_actions.short_description = 'Balance Actions'


@admin.register(CashoutRequest, site=admin_site)
class CashoutRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'payment_method', 'status', 'created_at', 'action_buttons']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'payment_method', 'payment_details', 'note']
    readonly_fields = ['user', 'amount', 'payment_method', 'payment_details', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'amount', 'status', 'note')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'payment_details')
        }),
        ('Admin Response', {
            'fields': ('admin_note', 'processed_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def action_buttons(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}">Approve</a> '
                '<a class="button" href="{}">Reject</a>',
                f'/admin/marketplace/cashoutrequest/{obj.id}/approve/',
                f'/admin/marketplace/cashoutrequest/{obj.id}/reject/'
            )
        return obj.status.upper()
    action_buttons.short_description = 'Actions'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:request_id>/approve/', self.admin_site.admin_view(self.approve_request), name='approve_cashout_request'),
            path('<int:request_id>/reject/', self.admin_site.admin_view(self.reject_request), name='reject_cashout_request'),
        ]
        return custom_urls + urls
    
    def approve_request(self, request, request_id):
        cashout_request = CashoutRequest.objects.get(id=request_id)
        
        if cashout_request.status == 'pending':
            # Get user's total earnings from completed orders
            from django.db.models import Sum
            total_earnings = Order.objects.filter(
                seller=cashout_request.user,
                status='completed'
            ).aggregate(total=Sum('price'))['total'] or 0
            
            # Get total already cashed out
            total_cashed_out = CashoutRequest.objects.filter(
                user=cashout_request.user,
                status='approved'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            available_earnings = total_earnings - total_cashed_out
            
            if cashout_request.amount > available_earnings:
                messages.error(request, f'Insufficient earnings! Available: {available_earnings} Taka, Requested: {cashout_request.amount} Taka')
                return redirect('admin:marketplace_cashoutrequest_changelist')
            
            # Create transaction record for cashout (does NOT affect balance)
            Transaction.objects.create(
                user=cashout_request.user,
                transaction_type='earning',
                amount=-cashout_request.amount,  # Negative to show cashout
                balance_after=cashout_request.user.profile.virtual_credits,  # Balance unchanged
                description=f'Earnings cashed out - {cashout_request.amount} Taka via {cashout_request.payment_method}'
            )
            
            # Update request status
            cashout_request.status = 'approved'
            cashout_request.processed_by = request.user
            cashout_request.admin_note = f'Approved by {request.user.username}. Payment processed to {cashout_request.payment_method}.'
            cashout_request.save()
            
            messages.success(request, f'Cashout approved! {cashout_request.user.username} will receive {cashout_request.amount} Taka via {cashout_request.payment_method}')
        else:
            messages.error(request, 'This request has already been processed.')
        
        return redirect('admin:marketplace_cashoutrequest_changelist')
    
    def reject_request(self, request, request_id):
        cashout_request = CashoutRequest.objects.get(id=request_id)
        
        if cashout_request.status == 'pending':
            cashout_request.status = 'rejected'
            cashout_request.processed_by = request.user
            cashout_request.admin_note = f'Rejected by {request.user.username}'
            cashout_request.save()
            
            messages.warning(request, f'Cashout request rejected for {cashout_request.user.username}')
        else:
            messages.error(request, 'This request has already been processed.')
        
        return redirect('admin:marketplace_cashoutrequest_changelist')
