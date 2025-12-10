# 🚀 Quick Start: Migrate to Supabase

## Why This is Easy!

Don't worry! I've automated everything for you. Just follow these simple steps:

## Prerequisites
- Your current MySQL database is working
- Python and pip are installed
- 10 minutes of your time

---

## 🎯 Super Easy Migration (Recommended)

### Step 1: Install Dependencies
```bash
pip install python-dotenv psycopg2-binary
```

### Step 2: Run the Migration Script
```bash
python migrate_to_supabase.py
```

The script will:
✅ Backup your MySQL data automatically
✅ Guide you through Supabase setup
✅ Configure everything for you
✅ Migrate all your data
✅ Create admin account

Just follow the prompts! 🎉

---

## 📋 Manual Steps (If you prefer)

### 1. Create Supabase Account (3 minutes)
1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub/Google (or email)

### 2. Create New Project (2 minutes)
1. Click "New Project"
2. Enter:
   - **Name**: `adezy`
   - **Database Password**: Make a strong one (SAVE IT!)
   - **Region**: Choose closest to you
3. Click "Create new project"
4. ☕ Wait 2-3 minutes (grab coffee!)

### 3. Get Connection Details (1 minute)
1. Click ⚙️ "Project Settings" (bottom left)
2. Click "Database" tab
3. Scroll to "Connection string"
4. You'll see something like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.abcdefgh.supabase.co:5432/postgres
   ```

**Write down:**
- **Host**: `db.abcdefgh.supabase.co` (yours will be different)
- **Password**: The password you created

### 4. Install PostgreSQL Driver
```bash
pip install psycopg2-binary python-dotenv
```

### 5. Backup Your MySQL Data
```bash
python manage.py dumpdata --natural-foreign --natural-primary --exclude=contenttypes --exclude=auth.Permission > backup.json
```

### 6. Create .env File
Create a file named `.env` in your project root with:
```env
USE_SUPABASE=True
SUPABASE_DB_HOST=db.abcdefgh.supabase.co
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your_password_here
SUPABASE_DB_PORT=5432
GEMINI_API_KEY=AIzaSyCJ4jiMs4rLF7obek2-3UrcqOQQQzdoK7k
```

### 7. Run Migrations
```bash
python manage.py migrate
```

### 8. Create Superuser
```bash
python manage.py createsuperuser
```

### 9. Import Data
```bash
python manage.py loaddata backup.json
```

### 10. Test It!
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## 🎉 Done!

You're now using Supabase! Benefits:
- ✅ No need to run XAMPP anymore
- ✅ Database is in the cloud
- ✅ Automatic daily backups
- ✅ More powerful (PostgreSQL > MySQL)
- ✅ Free tier is generous

---

## 🆘 Troubleshooting

### "dotenv module not found"
```bash
pip install python-dotenv
```

### "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### Migration fails
```bash
python manage.py migrate --run-syncdb
```

### Can't connect to Supabase
- Check your password is correct
- Verify the host URL (no spaces)
- Ensure you're using port 5432

### Data import fails
Try importing without auth data:
```bash
python manage.py dumpdata marketplace --natural-foreign > marketplace_only.json
python manage.py loaddata marketplace_only.json
```

---

## 📞 Still Stuck?

Check these files I created for you:
1. `SUPABASE_MIGRATION.md` - Detailed guide
2. `migrate_to_supabase.py` - Automated script
3. `.env.example` - Template for your .env file

Your professor will be impressed! 💪
