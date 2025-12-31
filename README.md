# AdEzy - Freelance Marketplace Platform

A Django-based freelance marketplace where users can offer and purchase services (gigs), similar to Fiverr. Built with Django 4.2.7 and PostgreSQL (Supabase).

## 🎯 Key Features

- 👤 **User Authentication**: Secure login/registration with separate admin and user sessions
- 🛍️ **Gig Management**: Create, update, browse, and filter service offerings by category
- 💬 **Messaging System**: Real-time messaging between buyers and sellers
- 📦 **Order Management**: Complete order lifecycle tracking and management
- ⭐ **Rating & Review System**: Rate gigs with featured/top-rated filtering
- 🔔 **Notifications**: Real-time notifications for orders, messages, and updates
- 🎨 **AI Content Generator**: 
  - Text-to-Text: Generate captions and hashtags for social media
  - Text-to-Image: Create product visuals from descriptions
- 🔍 **Advanced Search**: Real-time search with suggestions and filtering
- 💰 **Virtual Credits**: Balance management and admin approval system
- 📊 **Analytics Dashboard**: Track orders, earnings, and buyer/seller activities

## 🛠️ Tech Stack

- **Backend**: Django 4.2.7
- **Database**: PostgreSQL (Supabase Cloud)
- **Frontend**: HTML5, CSS3 (with animations), Vanilla JavaScript
- **AI APIs**: 
  - Google Gemini 2.0 Flash (via OpenRouter) - Text generation
  - ByteDance Seedream 4.5 (via OpenRouter) - Image generation
- **Static Files**: WhiteNoise
- **Image Processing**: Pillow

## 📁 Project Structure

```
AdEzy/
├── adezy/                  # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── marketplace/            # Main Django app
│   ├── models.py          # Database models
│   ├── views.py           # JSON API views
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin configuration
│   └── templates/
│       └── marketplace/
│           ├── base.html
│           ├── home.html
│           └── dashboard.html
├── static/
│   ├── css/
│   │   └── styles.css     # Modern CSS with animations
│   └── js/
│       └── main.js        # Client-side logic
├── manage.py
└── requirements.txt
```

## 🚀 Setup Instructions (Local Development)

### Prerequisites

- Python 3.12.6 or higher
- Git
- pip (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/YourUsername/AdEzy.git
cd AdEzy
```

### 2. Create Virtual Environment

**Windows (Git Bash):**
```bash
python -m venv venv
source venv/Scripts/activate
```

**Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# AdEzy Environment Variables

# Database Configuration
USE_SUPABASE=True

# Supabase Database Credentials - Session Pooler (IPv4)
SUPABASE_DB_HOST=aws-1-ap-southeast-1.pooler.supabase.com
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.friagzimveexfizdlmqf
SUPABASE_DB_PASSWORD=fahadsikder
SUPABASE_DB_PORT=5432

# Seedream API Configuration (ByteDance) - For Image Generation
SEEDREAM_API_KEY=
SEEDREAM_API_BASE=https://openrouter.ai/api/v1

# Gemini API Configuration - For Text Generation
GEMINI_API_KEY=
GEMINI_API_BASE=https://openrouter.ai/api/v1

```

> **Note**: Replace placeholder values with your actual credentials. Never commit the `.env` file to Git!

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Create Admin Account

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser!

### 8. Access Admin Panel

Visit `http://127.0.0.1:8000/admin/` and log in with your superuser credentials.

## 📋 Database Models

- **User**: Extended Django user model with authentication
- **UserProfile**: User profiles with virtual credits balance
- **Category**: Service categories (8 predefined)
- **Gig**: Service offerings with ratings and featured status
- **Order**: Purchase transactions and order management
- **Message**: Real-time user-to-user messaging
- **Transaction**: Payment and balance records
- **Review**: Service reviews and ratings
- **Notification**: User notifications and alerts
- **BalanceRequest**: Virtual credit top-up requests

## 🌐 Service Categories

The platform includes 8 pre-configured service categories:
- 📱 Social Media Marketing
- 🔍 Google Ads
- ✍️ Content Writing
- 🎨 Graphic Design
- 🎥 Video Ads
- 📧 Email Marketing
- 🔎 SEO Services
- 📊 Analytics & Reports

## 🎯 Usage Guide

### For Buyers
1. **Browse Services**: Explore gigs by category or search
2. **Filter Options**: Use "Top Rated", "New Arrivals", or category filters
3. **View Details**: Click on any gig to see full details and seller info
4. **Place Order**: Purchase gigs with virtual credits
5. **Message Sellers**: Communicate directly with service providers
6. **Track Orders**: Monitor order progress in your dashboard

### For Sellers
1. **Create Gigs**: Offer your services with detailed descriptions
2. **Set Pricing**: Define your service price and delivery time
3. **Manage Orders**: Track and fulfill orders from your dashboard
4. **Message Buyers**: Respond to buyer inquiries
5. **View Earnings**: Monitor your earnings and statistics

### Admin Features
- User management
- Gig approval and moderation
- Balance request approvals
- Category management
- Platform analytics

## 🎨 AI Content Generator

Access the **Imagine** section to use AI-powered tools:

### Text-to-Text Mode
- Generate engaging social media captions
- Create relevant hashtags
- Powered by Google Gemini 2.0 Flash

### Text-to-Image Mode
- Generate product images from descriptions
- Create visual content for gigs
- Po� Troubleshooting

### Common Issues

**Database Connection Error:**
- Verify your `.env` file has correct Supabase credentials
- Check if your IP is whitelisted in Supabase dashboard

**Static Files Not Loading:**
- Run `python manage.py collectstatic` if needed
- Check `DEBUG=True` in `.env` for development

**AI Features Not Working:**
- Verify `OPENROUTER_API_KEY` is set in `.env`
- Ensure you have API credits on OpenRouter

**Port Already in Use:**
- Use a different port: `python manage.py runserver 8080`
- Or kill the process using port 8000

## 📝 Project Structure Overview

```
AdEzy/
├── adezy/                      # Django project settings
│   ├── settings.py            # Main configuration
│   ├── urls.py                # Root URL routing
│   └── wsgi.py                # WSGI configuration
├── marketplace/               # Main application
│   ├── models.py             # Database models
│   ├── views.py              # API views and logic
│   ├── urls.py               # App URL routing
│   ├── admin.py              # Admin panel config
│   ├── middleware.py         # Custom middleware
│   └── templates/            # HTML templates
│       └── marketplace/
│           ├── base.html
│           ├── home.html
│           ├── gig_detail.html
│           ├── dashboard.html
│           ├── imagine.html
│           └── ...
├── static/                    # Static files
│   ├── css/
│   │   └── styles.css        # Main stylesheet
│   ├── js/
│   │   └── main.js           # Client-side logic
│   └── images/               # Static images
├── media/                     # User uploads
│   └── gigs/                 # Gig images
├── requirements.txt          # Python dependencies
├── manage.py                 # Django CLI
├── .env                      # Environment variables (create this)
└── .gitignore               # Git ignore rules
```

## 📄 License

This project is created for educational purposes.

## 📧 Contact & Credits

**Developer**: Fahad Sikder  
**GitHub**: [@FraggyKnowsCode](https://github.com/FraggyKnowsCode)

## 🙏 Acknowledgments

- Django Framework and Documentation
- Supabase (PostgreSQL Cloud Database)
- OpenRouter API Platform
- Google Gemini & ByteDance Seedream AI Models
- Modern CSS animations and design patterns

---

**Built with ❤️ for learning Django and full-stack develop
- Google Gemini AI
- Render.com Platform

---

**Built with ❤️ for learning Django and cloud deployment**
