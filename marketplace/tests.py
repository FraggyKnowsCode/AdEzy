from django.test import TestCase
from django.contrib.auth.models import User
from .models import UserProfile, Category, Gig, Order

# Create your tests here.

class UserProfileTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_user_profile_creation(self):
        """Test that user profile is created with default credits"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.virtual_credits, 1000.00)
        self.assertFalse(profile.is_seller_mode)


class GigTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='seller',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category')
        
    def test_gig_creation(self):
        """Test creating a gig"""
        gig = Gig.objects.create(
            seller=self.user,
            title='Test Gig',
            description='Test description',
            category=self.category,
            price=100.00,
            delivery_time=3,
            status='active'
        )
        self.assertEqual(gig.title, 'Test Gig')
        self.assertEqual(gig.price, 100.00)
        self.assertEqual(gig.status, 'active')
