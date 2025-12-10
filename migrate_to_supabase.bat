@echo off
REM AdEzy - Quick Supabase Migration for Windows

echo ==========================================
echo AdEzy - MySQL to Supabase Migration
echo ==========================================
echo.

echo Installing required packages...
pip install python-dotenv psycopg2-binary
echo.

echo ==========================================
echo STEP 1: Create Supabase Account
echo ==========================================
echo.
echo Please open your browser and:
echo 1. Go to https://supabase.com
echo 2. Sign up for free account
echo 3. Create new project named 'adezy'
echo 4. Choose a database password and SAVE IT!
echo 5. Wait 2-3 minutes for project creation
echo.
pause

echo.
echo ==========================================
echo STEP 2: Get Connection Details
echo ==========================================
echo.
echo In Supabase:
echo 1. Click Settings (gear icon)
echo 2. Click 'Database' tab
echo 3. Find your connection details
echo.

set /p SUPABASE_HOST="Enter your Supabase Host (e.g., db.xxxxx.supabase.co): "
set /p SUPABASE_PASSWORD="Enter your database password: "

echo.
echo Creating .env file...
(
echo USE_SUPABASE=True
echo SUPABASE_DB_HOST=%SUPABASE_HOST%
echo SUPABASE_DB_NAME=postgres
echo SUPABASE_DB_USER=postgres
echo SUPABASE_DB_PASSWORD=%SUPABASE_PASSWORD%
echo SUPABASE_DB_PORT=5432
echo GEMINI_API_KEY=AIzaSyCJ4jiMs4rLF7obek2-3UrcqOQQQzdoK7k
) > .env

echo Done!
echo.

echo ==========================================
echo STEP 3: Backup MySQL Data
echo ==========================================
python manage.py dumpdata --natural-foreign --natural-primary --exclude=contenttypes --exclude=auth.Permission > mysql_backup.json
echo Backup created: mysql_backup.json
echo.

echo ==========================================
echo STEP 4: Migrate to Supabase
echo ==========================================
python manage.py migrate
echo.

echo ==========================================
echo STEP 5: Create Superuser
echo ==========================================
python manage.py createsuperuser
echo.

echo ==========================================
echo STEP 6: Import Data
echo ==========================================
python manage.py loaddata mysql_backup.json
echo.

echo ==========================================
echo MIGRATION COMPLETE!
echo ==========================================
echo.
echo Your app is now using Supabase!
echo.
echo Test it:
echo   python manage.py runserver
echo.
echo Visit: http://127.0.0.1:8000
echo.
echo You can now turn off XAMPP!
echo.
pause
