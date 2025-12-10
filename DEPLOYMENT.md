# AdEzy Deployment Guide for Render.com

## Prerequisites
- GitHub account
- Render.com account (free)
- Supabase database (already set up)

## Step 1: Push Code to GitHub

1. **Initialize Git** (if not already done):
   ```bash
   cd /c/Users/User/Desktop/AdEzy
   git init
   git add .
   git commit -m "Initial commit - AdEzy marketplace"
   ```

2. **Create a new repository on GitHub**:
   - Go to https://github.com/new
   - Name it: `adezy-marketplace`
   - Don't initialize with README
   - Click "Create repository"

3. **Push your code**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/adezy-marketplace.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy to Render

1. **Go to Render.com**:
   - Visit https://render.com
   - Sign up/Login with GitHub

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `adezy-marketplace`
   - Click "Connect"

3. **Configure the service**:
   - **Name**: `adezy-marketplace`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `sh build.sh`
   - **Start Command**: `gunicorn adezy.wsgi:application`
   - **Instance Type**: `Free`

4. **Add Environment Variables** (Click "Advanced" → "Add Environment Variable"):
   ```
   USE_SUPABASE=True
   SUPABASE_DB_HOST=aws-1-ap-southeast-1.pooler.supabase.com
   SUPABASE_DB_NAME=postgres
   SUPABASE_DB_USER=postgres.friagzimveexfizdlmqf
   SUPABASE_DB_PASSWORD=fahadsikder
   SUPABASE_DB_PORT=5432
   GEMINI_API_KEY=AIzaSyCJ4jiMs4rLF7obek2-3UrcqOQQQzdoK7k
   SECRET_KEY=your-secret-key-here-make-it-random-and-long
   DEBUG=False
   PYTHON_VERSION=3.12.6
   ```

5. **Add ALLOWED_HOSTS and CSRF** (after you get your Render URL):
   ```
   ALLOWED_HOSTS=your-app-name.onrender.com
   CSRF_TRUSTED_ORIGINS=https://your-app-name.onrender.com
   ```

6. **Click "Create Web Service"**

## Step 3: Wait for Deployment
- Render will build and deploy your app (takes 5-10 minutes first time)
- You'll get a URL like: `https://adezy-marketplace.onrender.com`
- Your website will be live 24/7! 🎉

## Step 4: Create Admin Account
After deployment, create your admin account:
1. Go to Render dashboard → Your service → "Shell"
2. Run: `python manage.py createsuperuser`

## Updating Your Site
Whenever you make changes:
```bash
git add .
git commit -m "Your update description"
git push
```
Render will automatically redeploy!

## Important Notes:
- ✅ Free tier includes 750 hours/month (enough for demos)
- ✅ Your site stays online 24/7
- ✅ Automatic HTTPS
- ⚠️  Free tier sleeps after 15 minutes of inactivity (wakes up in ~30 seconds)
- ⚠️  Free tier expires after 90 days (just redeploy)

## Your professor can access:
`https://your-app-name.onrender.com` from anywhere!
