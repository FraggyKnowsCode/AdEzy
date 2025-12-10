# AdEzy - Freelance Marketplace Platform

A Django-based freelance marketplace where users can offer and purchase services (gigs), similar to Fiverr. Built with Django 4.2.7 and PostgreSQL (Supabase).

## 🎯 Key Features

- 👤 **User Authentication**: Separate sessions for admin and regular users
- 🛍️ **Gig Management**: Create, update, and browse service offerings
- 💬 **Messaging System**: Direct communication between buyers and sellers
- 📦 **Order Management**: Track orders and transactions
- ⭐ **Review System**: Rate and review completed services
- 🔔 **Notifications**: Real-time notifications for important events
- 🤖 **AI Integration**: Gemini API for enhanced features
- 📊 **Admin Dashboard**: Comprehensive admin panel for platform management

## 🛠️ Tech Stack

- **Backend**: Django 4.2.7
- **Database**: PostgreSQL (Supabase Cloud)
- **Frontend**: HTML, CSS, JavaScript
- **API**: Google Gemini AI
- **Deployment**: Render.com
- **Static Files**: WhiteNoise

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

## 🚀 Setup Instructions

### Prerequisites

- Python 3.12.6 or higher
- Git
- pip (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/FraggyKnowsCode/AdEzy.git
cd AdEzy
```

### 2. Create Virtual Environment

**Windows (Git Bash):**
```bash
python -m venv venv
source venv/Scripts/activate
```

**Windows (CMD):**
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

Create a `.env` file in the project root:

```env
USE_SUPABASE=True
SUPABASE_DB_HOST=aws-1-ap-southeast-1.pooler.supabase.com
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.friagzimveexfizdlmqf
SUPABASE_DB_PASSWORD=your_password_here
SUPABASE_DB_PORT=5432
GEMINI_API_KEY=your_gemini_api_key_here
DEBUG=True
SECRET_KEY=your_secret_key_here
```

### 5. Run Migrations (Optional)

Database migrations are already applied on Supabase. If needed:

```bash
python manage.py migrate
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see the app!

## 📋 Database Models

- **User**: Extended Django user model
- **UserProfile**: User profile with additional information
- **Category**: Service categories (8 predefined categories)
- **Gig**: Service offerings
- **Order**: Purchase transactions
- **Message**: User-to-user messaging
- **Transaction**: Payment records
- **Review**: Service reviews and ratings
- **Notification**: User notifications

## 📂 Project Structure

```
AdEzy/
├── adezy/                  # Main project settings
│   ├── settings.py         # Django settings with Supabase config
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI configuration
├── marketplace/           # Main application
│   ├── models.py          # Database models
│   ├── views.py           # View logic
│   ├── urls.py            # App URL routing
│   ├── admin.py           # Admin configuration
│   ├── middleware.py      # Custom middleware for sessions
│   └── templates/         # HTML templates
├── static/               # Static files (CSS, JS, images)
├── media/                # User uploaded files
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
├── Procfile             # Render.com deployment config
├── build.sh             # Build script for deployment
└── runtime.txt          # Python version specification
```

## 🌐 Categories

The platform includes 8 service categories:
- Social Media Marketing
- Google Ads
- Content Writing
- Graphic Design
- Video Ads
- Email Marketing
- SEO Services
- Analytics & Reports

## 🚀 Deployment

The application is deployed on Render.com and uses Supabase for the database.

**Live URL**: [https://adezy.onrender.com](https://adezy.onrender.com) (if deployed)

### Deploy to Render

1. Fork/Clone this repository
2. Create a new Web Service on Render.com
3. Connect your GitHub repository
4. Configure environment variables (same as `.env` file)
5. Render will automatically deploy using `build.sh` and `Procfile`

## 🎯 Usage

### Admin Panel
Access the admin panel at `/admin/` with superuser credentials.

### User Registration
New users can register at `/register/` and start offering or purchasing services.

### Creating a Gig
1. Log in to your account
2. Navigate to Dashboard
3. Click "Create Gig"
4. Fill in service details and submit

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is created for educational purposes.

## 📧 Contact

**Developer**: Fahad Sikder  
**GitHub**: [@FraggyKnowsCode](https://github.com/FraggyKnowsCode)  
**Repository**: [AdEzy](https://github.com/FraggyKnowsCode/AdEzy)

## 🙏 Acknowledgments

- Django Documentation
- Supabase Documentation
- Google Gemini AI
- Render.com Platform

---

**Built with ❤️ for learning Django and cloud deployment**
