# AdEzy - Digital Growth & Services Marketplace 🚀

[![Django](https://img.shields.io/badge/Django-4.2.7-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/Supabase_PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![Vercel](https://img.shields.io/badge/Deployed_on-Vercel-black?style=for-the-badge&logo=vercel&logoColor=white)](https://adezy.vercel.app)
[![OpenRouter](https://img.shields.io/badge/AI-Gemini_%26_Seedream-blueviolet?style=for-the-badge)](https://openrouter.ai/)

**AdEzy** is a modern, full-stack digital services and products marketplace connecting creators, businesses, and entrepreneurs. Built with Django, Supabase PostgreSQL, and modern glassmorphism dark-mode UI, AdEzy features AI-powered content generation, instant gig purchasing, real-time messaging, and virtual wallet transactions.

🌐 **Live Demo:** [https://adezy.vercel.app](https://adezy.vercel.app)

---

## ✨ Key Features

- 🛒 **Service & Product Marketplace**:
  - Browse 8+ categories (Social Media Marketing, Google Ads, Graphic Design, Video Ads, Content Writing, SEO, Analytics, etc.).
  - Search, filter by ratings, new arrivals, price ranges, and categories.
  - Detailed product/gig views with portfolios, client reviews, FAQs, and pricing tiers.
- 🎨 **"Imagine" AI Content Studio**:
  - **Text-to-Text**: Generate viral captions, ad copy, and targeted hashtags powered by Google Gemini 2.0 Flash (via OpenRouter).
  - **Text-to-Image**: Generate photorealistic marketing visuals and digital art powered by ByteDance Seedream 4.5.
- 💬 **Messaging & WhatsApp Integration**:
  - Built-in user-to-user messaging with file attachments.
  - One-click direct WhatsApp chat modal with sellers.
- 💰 **Virtual Wallet & Credits**:
  - In-platform balance system with transaction logs.
  - Deposit request workflow with administrative review and approvals.
- 🛡️ **Dual-Session Architecture**:
  - Separate authentication middleware allowing admins and regular users to maintain concurrent isolated sessions.
- ⚡ **Cloud Database & Edge Deployment**:
  - Cloud PostgreSQL hosted on **Supabase** with connection pooling.
  - Serverless Python deployment on **Vercel** with **WhiteNoise** static asset distribution.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | Django 4.2.7 (Python 3.12) |
| **Database** | Supabase (PostgreSQL 15+ via Transaction & Session Poolers) |
| **Frontend** | HTML5, Vanilla CSS3 (Custom Glassmorphism Dark Theme), JavaScript |
| **Icons & Fonts** | FontAwesome 6, Google Fonts (Outfit & Plus Jakarta Sans) |
| **AI Integration** | OpenRouter API (Google Gemini 2.0 Flash & ByteDance Seedream 4.5) |
| **Static & Media** | WhiteNoise 6.6.0 + Vercel Edge CDN |
| **Hosting** | Vercel Serverless Functions (`@vercel/python` & `@vercel/static-build`) |

---

## 📁 Project Structure

```
AdEzy/
├── adezy/                         # Django project core
│   ├── settings.py                # Database, WhiteNoise, & API settings
│   ├── urls.py                    # Root routing
│   └── wsgi.py                    # WSGI entrypoint with WhiteNoise fallback
├── marketplace/                   # Main marketplace application
│   ├── models.py                  # UserProfile, Gig, Product, Order, Message, etc.
│   ├── views.py                   # Marketplace views, cart, checkout, and AI studio
│   ├── urls.py                    # Marketplace routing
│   ├── middleware.py              # Isolated admin session middleware
│   ├── supabase_auth.py           # Supabase auth & identity sync
│   └── templates/marketplace/     # UI templates
├── static/                        # Static assets
│   ├── css/styles.css             # Ultra-premium responsive dark theme
│   └── js/main.js                 # Cart, modals, AI generation, and interactivity
├── media/                         # Media files & gig thumbnails
├── build_files.sh                 # Vercel build script (collectstatic & asset sync)
├── vercel.json                    # Vercel routing & serverless configuration
├── runtime.txt                    # Python 3.12.6 runtime definition
├── requirements.txt               # Dependencies
└── manage.py
```

---

## 🚀 Local Development Setup

### 1. Prerequisites
- **Python**: 3.12+
- **Git**: Installed on your system
- **Supabase Account**: (or local PostgreSQL / SQLite)

### 2. Clone Repository
```bash
git clone https://github.com/FraggyKnowsCode/AdEzy.git
cd AdEzy
```

### 3. Create & Activate Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the root folder:

```env
# Supabase API
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
SUPABASE_SECRET_KEY=sb_secret_...
SUPABASE_JWKS_URL=https://your-project-ref.supabase.co/auth/v1/.well-known/jwks.json

# Supabase Database Pooler
USE_SUPABASE=True
USE_SQLITE=False
SUPABASE_DB_HOST=aws-0-ap-south-1.pooler.supabase.com
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.your-project-ref
SUPABASE_DB_PASSWORD=your_database_password
SUPABASE_DB_PORT=6543

# Django Settings
DEBUG=True
SECRET_KEY=django-insecure-your-local-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost,.vercel.app,*
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000,https://*.vercel.app

# AI APIs (Optional - for "Imagine" studio)
SEEDREAM_API_KEY=your_openrouter_key
SEEDREAM_API_BASE=https://openrouter.ai/api/v1
GEMINI_API_KEY=your_openrouter_key
GEMINI_API_BASE=https://openrouter.ai/api/v1
```

### 6. Run Migrations & Superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Run Local Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000` to browse the store and `http://127.0.0.1:8000/admin` for the admin panel.

---

## ☁️ Deploying to Vercel

1. Push your repository to GitHub.
2. Connect your repository to **[Vercel](https://vercel.com/)**.
3. Under **Project Settings** → **Environment Variables**, paste the production variables (with `DEBUG=False` and your Supabase connection credentials).
4. Deploy! Vercel automatically runs `build_files.sh`, compiles static assets, and deploys the WSGI serverless function.

---

## 👤 Author

**Fahad Sikder**
- GitHub: [@FraggyKnowsCode](https://github.com/FraggyKnowsCode)

---

## 📄 License

This project is licensed for educational and portfolio demonstration purposes.
