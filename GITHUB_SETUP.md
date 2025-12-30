# GitHub Setup Guide - Push AdEzy to GitHub

This guide will help you push your AdEzy project to GitHub and share it with your friends.

## 📋 Prerequisites

- Git installed on your computer
- GitHub account (create one at [github.com](https://github.com) if needed)
- Your project is ready and tested locally

## 🚀 Step-by-Step Instructions

### Step 1: Create a New Repository on GitHub

1. Go to [github.com](https://github.com) and log in
2. Click the **"+"** icon in the top right corner
3. Select **"New repository"**
4. Configure your repository:
   - **Repository name**: `AdEzy` (or any name you prefer)
   - **Description**: "Django-based freelance marketplace with AI features"
   - **Visibility**: Choose **Public** or **Private**
   - **DO NOT** check "Initialize with README" (we already have one)
5. Click **"Create repository"**

### Step 2: Initialize Git (if not already done)

Open Git Bash or terminal in your project folder:

```bash
cd /c/Users/User/Desktop/AdEzy
```

Check if Git is already initialized:
```bash
git status
```

If you see "fatal: not a git repository", initialize it:
```bash
git init
```

### Step 3: Add Files to Git

```bash
# Add all files (respects .gitignore)
git add .

# Check what will be committed
git status
```

**Important**: Make sure `.env` is NOT listed (it should be ignored by .gitignore)!

### Step 4: Create Initial Commit

```bash
git commit -m "Initial commit: AdEzy Marketplace with AI features"
```

### Step 5: Connect to GitHub Repository

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/AdEzy.git
```

Verify the remote was added:
```bash
git remote -v
```

### Step 6: Push to GitHub

```bash
# Rename branch to main (if needed)
git branch -M main

# Push code to GitHub
git push -u origin main
```

You may be prompted to log in to GitHub. Use your credentials or a personal access token.

### Step 7: Verify Upload

1. Go to your GitHub repository in your browser
2. Refresh the page
3. You should see all your files uploaded!

## 🔐 Security Checklist

Before pushing, ensure these files are **NOT** visible in your Git status:

- ❌ `.env` (contains sensitive credentials)
- ❌ `venv/` or `env/` (virtual environment)
- ❌ `__pycache__/` (Python cache)
- ❌ `*.pyc` files
- ❌ `media/` folder (user uploads)
- ❌ `db.sqlite3` (if using local database)

If any of these appear in `git status`, they're not being ignored properly!

## 📤 Sharing with Friends

Once pushed to GitHub, your friends can clone it:

```bash
git clone https://github.com/YOUR_USERNAME/AdEzy.git
cd AdEzy
```

**Important**: They will need to:
1. Create their own `.env` file (use `.env.example` as a template)
2. Get database credentials from you
3. Get API keys from you
4. Follow the setup instructions in `DEPLOYMENT.md`

## 🔄 Updating Your Repository

When you make changes later:

```bash
# Check what changed
git status

# Add changes
git add .

# Commit with a descriptive message
git commit -m "Add new feature: describe what you changed"

# Push to GitHub
git push
```

## 🆘 Common Issues

### Issue: "Permission denied (publickey)"
**Solution**: Set up SSH keys or use HTTPS with personal access token

### Issue: "Remote origin already exists"
**Solution**: Remove and re-add the remote
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/AdEzy.git
```

### Issue: "Failed to push some refs"
**Solution**: Pull first, then push
```bash
git pull origin main --rebase
git push origin main
```

### Issue: ".env file is visible in Git"
**Solution**: Remove it from Git tracking
```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
git push
```

## 📋 What Gets Pushed to GitHub

✅ **Included:**
- Python code files (.py)
- HTML templates
- CSS and JavaScript files
- Static images
- Requirements.txt
- README.md and documentation
- Configuration files (settings.py, urls.py, etc.)
- .gitignore
- .env.example (template)

❌ **Excluded (by .gitignore):**
- .env (credentials)
- venv/ (virtual environment)
- __pycache__/ (Python cache)
- media/ (user uploads)
- *.pyc files
- Database files
- IDE settings

## 🎯 Best Practices

1. **Commit often** with clear messages
2. **Never commit sensitive data** (passwords, API keys)
3. **Use .gitignore** properly
4. **Test locally** before pushing
5. **Write descriptive commit messages**
6. **Keep README updated**

## 📝 Good Commit Message Examples

```bash
git commit -m "Add pagination to gig listings"
git commit -m "Fix footer not showing on gig detail page"
git commit -m "Update AI API integration with OpenRouter"
git commit -m "Improve search functionality with filters"
```

## 🌟 After Pushing

Your repository URL will be:
```
https://github.com/YOUR_USERNAME/AdEzy
```

Share this URL with your friends, and they can clone and run the project following the `DEPLOYMENT.md` guide!

---

**Happy Coding! 🚀**
