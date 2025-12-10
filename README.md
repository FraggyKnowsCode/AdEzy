# AdEzy - Freelance Marketplace for Online Ad Services

A Django-based freelance marketplace with a **JavaScript-first architecture**, focusing on client-side rendering and dynamic DOM manipulation.

## 🎯 Key Features

- **Buyer/Seller Profile Switching**: Users can switch between buyer and seller modes
- **Virtual Credit System**: Demo-friendly currency system (no real money)
- **Client-Side Rendering**: JavaScript fetches JSON and dynamically builds the UI
- **Modern CSS**: Custom CSS with variables, animations, and glass-morphism effects
- **No Page Reloads**: Search filtering and tab switching handled entirely in JavaScript

## 🛠️ Tech Stack

- **Backend**: Python 3.x, Django 4.2
- **Database**: MySQL
- **Frontend**: Vanilla JavaScript (ES6+), Custom CSS (Flexbox/Grid)
- **Styling**: CSS Variables, Animations, Backdrop Filters

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

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure MySQL Database

Update `adezy/settings.py` with your MySQL credentials:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'adezy_db',
        'USER': 'your_mysql_username',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

Create the database:

```sql
CREATE DATABASE adezy_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Create Sample Data

After creating a superuser, log in to the Django admin panel and create:

1. **Categories**: e.g., "Social Media Marketing", "Google Ads", "SEO", "Content Writing"
2. **User Profiles**: Create profiles for test users with virtual credits
3. **Gigs**: Create sample gigs with images, prices, and descriptions

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see the app!

## 📋 Database Models

### UserProfile
- Links to Django User model
- Tracks virtual credits balance
- Boolean flag for buyer/seller mode switching

### Gig
- Title, description, price, delivery time
- Links to seller (User) and Category
- Image field for gig thumbnails
- Status field (active/paused/draft)

### Order
- Links buyer, seller, and gig
- Tracks order status (pending → in_progress → delivered → completed)
- Stores requirements and delivery notes

### Transaction
- Records all virtual credit movements
- Types: credit, debit, refund, earning
- Links to related order

### Review
- One review per order
- Rating (1-5 stars) and comment

## 🎨 CSS Architecture

### CSS Variables (`:root`)
```css
--deep-blue: #0f172a
--gold: #fbbf24
--white: #ffffff
```

### Key Classes
- `.gig-card`: Grid-based card with hover effects
- `.glass-panel`: Backdrop-filter glass-morphism effect
- `.modal`: Animated modal with fade-in
- `.tab-btn`: Dashboard tab switching buttons

### Animations
- `@keyframes fade-in`: Smooth entrance for dynamic elements
- `@keyframes spin`: Loading spinner
- `@keyframes checkmark-stroke`: Success checkmark animation

## 💻 JavaScript Architecture

### Core Functions

**`loadGigs()`**
- Fetches gigs from `/api/gigs/`
- Uses `document.createElement()` to build DOM
- Applies `fade-in` animation with staggered delays

**`renderGigs(gigs)`**
- Clears container with `innerHTML = ''`
- Iterates through gigs array
- Creates card elements dynamically

**`setupSearchListener()`**
- Listens to search input
- Filters `allGigs` array client-side
- Re-renders without page reload

**`handleOrder(gigId)`**
- Shows modal with loading spinner
- Simulates 2-second delay with `setTimeout()`
- Sends POST request to `/api/orders/create/`
- Shows success checkmark or error message
- Updates navbar balance via DOM manipulation

**`setupDashboardTabs()`**
- Selects all `.tab-btn` elements
- Toggles `.active` class on click
- Shows/hides sections with CSS transitions

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/gigs/` | Get all active gigs (JSON) |
| GET | `/api/gigs/<id>/` | Get single gig details |
| POST | `/api/orders/create/` | Create new order |
| GET | `/api/orders/buyer/` | Get user's purchases |
| GET | `/api/orders/seller/` | Get user's sales |
| GET | `/api/user/balance/` | Get current balance |
| GET | `/api/categories/` | Get all categories |

## 🎓 Educational Goals

This project demonstrates:

✅ **Separation of Concerns**: Django serves data (JSON), JavaScript handles presentation  
✅ **Modern JavaScript**: Fetch API, async/await, DOM manipulation, event delegation  
✅ **CSS Skills**: Variables, Grid, Flexbox, animations, pseudo-elements  
✅ **RESTful API Design**: Clean JSON endpoints  
✅ **State Management**: Global `allGigs` array, filtering without backend calls  
✅ **User Experience**: Loading states, error handling, smooth transitions  

## 📝 Next Steps

- [ ] Add user authentication views (login/register)
- [ ] Implement profile switching UI
- [ ] Add file upload for gig creation
- [ ] Build order status update functionality
- [ ] Add real-time notifications
- [ ] Implement review system UI

## 🎯 University Demo Tips

1. **Showcase JavaScript Skills**: Emphasize how search works without reloading
2. **Explain CSS Animations**: Demonstrate fade-in and checkmark animations
3. **Highlight API Design**: Show how JSON endpoints work with fetch()
4. **Demo Virtual Credits**: Show order flow and balance updates
5. **Show Responsive Design**: Test on different screen sizes

## 📄 License

Educational project for university coursework.

---

**Built with ❤️ for learning JavaScript, CSS, and Django integration**
