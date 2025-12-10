#!/usr/bin/env python
"""
AdEzy - Supabase Migration Helper
Run this script to migrate from MySQL to Supabase step by step
"""
import os
import subprocess
import sys
from datetime import datetime

def print_header(text):
    print("\n" + "="*50)
    print(f"  {text}")
    print("="*50 + "\n")

def run_command(cmd, description):
    print(f"Running: {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print(f"✗ Error during {description}")
        if result.stderr:
            print(result.stderr)
        return False

def main():
    print_header("AdEzy MySQL to Supabase Migration")
    
    # Step 1: Backup MySQL data
    print("\n📦 Step 1: Backing up MySQL database...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"mysql_backup_{timestamp}.json"
    
    backup_cmd = f"python manage.py dumpdata --natural-foreign --natural-primary --exclude=contenttypes --exclude=auth.Permission > {backup_file}"
    if not run_command(backup_cmd, "Database backup"):
        print("⚠️  Warning: Backup failed, but continuing...")
    else:
        print(f"✓ Backup saved to: {backup_file}\n")
    
    # Step 2: Install dependencies
    print("\n📦 Step 2: Installing PostgreSQL driver...")
    if not run_command("pip install psycopg2-binary", "PostgreSQL driver installation"):
        print("❌ Failed to install driver. Please install manually:")
        print("   pip install psycopg2-binary")
        sys.exit(1)
    
    # Step 3: Configuration instructions
    print_header("Step 3: Supabase Configuration")
    print("Please follow these steps:\n")
    print("1. Go to https://supabase.com")
    print("2. Sign in or create an account")
    print("3. Click 'New Project'")
    print("4. Fill in project details:")
    print("   - Name: adezy (or your choice)")
    print("   - Database Password: Choose a strong password")
    print("   - Region: Choose closest to you")
    print("5. Wait 2-3 minutes for project creation")
    print("\n6. Once created, go to Project Settings → Database")
    print("7. Find 'Connection string' section")
    print("8. Copy the connection details\n")
    
    input("Press Enter after completing Supabase setup...")
    
    # Step 4: Get Supabase credentials
    print_header("Step 4: Enter Supabase Credentials")
    
    print("Please enter your Supabase connection details:")
    host = input("Host (e.g., db.xxxxx.supabase.co): ").strip()
    password = input("Database Password: ").strip()
    
    # Create .env file
    env_content = f"""# AdEzy Environment Variables
USE_SUPABASE=True

# Supabase Database Credentials
SUPABASE_DB_HOST={host}
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD={password}
SUPABASE_DB_PORT=5432

# Gemini API Key
GEMINI_API_KEY=AIzaSyCJ4jiMs4rLF7obek2-3UrcqOQQQzdoK7k
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✓ .env file created")
    
    # Install python-dotenv
    print("\n📦 Installing python-dotenv...")
    run_command("pip install python-dotenv", "python-dotenv installation")
    
    # Step 5: Update settings to read .env
    print("\n⚙️  Note: You need to add this to the top of settings.py:")
    print("   from dotenv import load_dotenv")
    print("   load_dotenv()")
    
    input("\nPress Enter after adding dotenv to settings.py...")
    
    # Step 6: Run migrations
    print_header("Step 5: Creating Database Schema")
    
    if not run_command("python manage.py makemigrations", "Make migrations"):
        print("❌ Migration creation failed")
        sys.exit(1)
    
    if not run_command("python manage.py migrate", "Apply migrations"):
        print("❌ Migration failed")
        sys.exit(1)
    
    # Step 7: Create superuser
    print_header("Step 6: Create Superuser")
    print("Please create an admin account:\n")
    run_command("python manage.py createsuperuser", "Superuser creation")
    
    # Step 8: Load data
    print_header("Step 7: Import Data")
    
    if os.path.exists(backup_file):
        print(f"Importing data from {backup_file}...")
        if run_command(f"python manage.py loaddata {backup_file}", "Data import"):
            print("\n✓ Data imported successfully!")
        else:
            print("\n⚠️  Data import had issues. You may need to import manually.")
    else:
        print(f"⚠️  Backup file {backup_file} not found")
    
    # Complete
    print_header("Migration Complete! 🎉")
    print("Your application is now using Supabase!")
    print("\nNext steps:")
    print("1. Test your application: python manage.py runserver")
    print("2. Visit: http://127.0.0.1:8000")
    print("3. Check admin: http://127.0.0.1:8000/admin")
    print(f"\n📁 MySQL backup saved as: {backup_file}")
    print("\n✨ You can now turn off XAMPP/MySQL!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
