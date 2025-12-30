# AdEzy - Local Setup Guide for GitHub Sharing

This guide explains how to run AdEzy on your friend's computer after cloning from GitHub.

**✅ 100% Compatible with Windows, Mac, and Linux!**

## 📋 System Requirements

- **Python**: 3.12.6 or higher
- **Git**: Latest version
- **Operating System**: Windows, macOS, or Linux (all supported!)
- **RAM**: Minimum 4GB recommended
- **Internet**: Required for database connection and AI features

## 🚀 Step-by-Step Setup

### Step 1: Install Python

**Windows:**
```bash
# Check if Python is installed
python --version

# Download from python.org if needed
```

**Mac:**
```bash
# Check if Python 3 is installed
python3 --version

# Install via Homebrew (recommended)
brew install python@3.12

# Or download from python.org
```

**Note for Mac users:** You may need to use `python3` and `pip3` instead of `python` and `pip`.

### Step 2: Clone the Repository

```bash
git clone https://github.com/YourUsername/AdEzy.git
cd AdEzy
```

### Step 3: Create Virtual Environment

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
python3 -m venv venv
source venv/bin/activate
```

> **Mac Users:** See [MAC_COMPATIBILITY.md](MAC_COMPATIBILITY.md) for detailed Mac setup guide!

> **Note**: You should see `(venv)` appear at the beginning of your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages:
- Django 4.2.7
- PostgreSQL adapter
- Image processing libraries
- AI API clients
- Static file handlers

### Step 5: Configure Environment Variables

Create a `.env` file in the project root directory:

```env
# Database Configuration (Supabase PostgreSQL)
USE_SUPABASE=True
SUPABASE_DB_HOST=your-supabase-host.pooler.supabase.com
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=your-database-user
SUPABASE_DB_PASSWORD=your-database-password
SUPABASE_DB_PORT=5432

# AI API Configuration (OpenRouter)
OPENROUTER_API_KEY=your-openrouter-api-key

# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here-make-it-long-and-random
ALLOWED_HOSTS=localhost,127.0.0.1
```

> **Important**: Get the actual credentials from the project owner! The `.env` file is not included in the GitHub repository for security reasons.

### Step 6: Run Database Migrations

```bash
python manage.py migrate
```

This will set up all necessary database tables on Supabase.

### Step 7: Create Admin Account (Optional)

If you need admin access:
```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### Step 8: Run the Development Server

```bash
python manage.py runserver
```

You should see output like:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Step 9: Access the Application

Open your web browser and navigate to:
- **Homepage**: `http://127.0.0.1:8000/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/`

## 🔧 Troubleshooting

### Issue: "python: command not found"
**Solution**: 
- **Mac/Linux**: Use `python3` instead of `python`
- **Windows**: Install Python from python.org

### Issue: "pip: command not found"
**Solution**: 
- **Mac/Linux**: Use `pip3` instead of `pip`
- **Windows**: Use `python -m pip` instead of `pip`

### Issue: Database connection error
**Solution**: 
1. Verify `.env` file has correct credentials
2. Check your internet connection
3. Ensure Supabase database is accessible

### Issue: Port 8000 already in use
**Solution**: 
```bash
# Windows/Mac/Linux
python manage.py runserver 8080

# Then access at http://127.0.0.1:8080/
```

### Issue: Static files not loading
**Solution**: Make sure `DEBUG=True` in your `.env` file

### Issue: AI features not working
**Solution**: Verify `OPENROUTER_API_KEY` is correctly set in `.env`

### Issue: Pillow installation error (Mac)
**Solution**:
```bash
# Install dependencies via Homebrew
brew install libjpeg zlib
pip install Pillow
```

### Issue: psycopg2 build error (Mac)
**Solution**:
```bash
# Install PostgreSQL dependencies
brew install postgresql
# Then try again
pip install -r requirements.txt
```

### 🍎 Mac-Specific Issues?
See [MAC_COMPATIBILITY.md](MAC_COMPATIBILITY.md) for comprehensive Mac troubleshooting!

## 📦 What's Included

- ✅ Full Django application code
- ✅ Database models and migrations
- ✅ Frontend templates (HTML/CSS/JS)
- ✅ AI integration for text and image generation
- ✅ User authentication system
- ✅ Messaging and notification system
- ✅ Order management
- ✅ Admin panel

## 🚫 What's NOT Included (for security)

- ❌ `.env` file (contains sensitive credentials)
- ❌ Database file (using cloud PostgreSQL)
- ❌ Media files (user uploads)
- ❌ Virtual environment folder
- ❌ Python bytecode cache files

## 🔒 Security Notes

1. **Never commit the `.env` file** to GitHub
2. **Keep API keys private** - don't share them publicly
3. **Change DEBUG to False** for production deployment
4. **Use strong SECRET_KEY** - generate a random one
5. **Protect database credentials** - don't expose them

## 🌐 Sharing on Local Network

To access from other devices on the same network:

1. Find your local IP address:
   - **Windows**: `ipconfig` (look for IPv4 Address)
   - **Mac/Linux**: `ifconfig` or `ip addr`

2. Update `.env`:
   ```env
   ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.XXX
   ```

3. Run server with your local IP:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

4. Access from other devices:
   ```
   http://192.168.1.XXX:8000/
   ```

## 📝 Development Tips

- Keep your virtual environment activated when working
- Run `python manage.py migrate` after pulling new code that includes migrations
- Use `git pull` regularly to get the latest updates
- Test features locally before sharing with others

## 🆘 Need Help?

If you encounter issues:
1. Check the error message in the terminal
2. Verify all dependencies are installed
3. Ensure `.env` file is properly configured
4. Check that the database is accessible
5. Review the troubleshooting section above

## 📚 Useful Commands

```bash
# Activate virtual environment
source venv/Scripts/activate  # Windows Git Bash
venv\Scripts\activate         # Windows CMD

# Install new packages
pip install package-name

# Update requirements.txt (if you add new packages)
pip freeze > requirements.txt

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run on different port
python manage.py runserver 8080

# Stop the server
CTRL + C
```

---

**Happy Coding! 🚀**
