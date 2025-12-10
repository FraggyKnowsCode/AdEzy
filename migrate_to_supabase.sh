#!/bin/bash
# AdEzy Database Migration Script - MySQL to Supabase

echo "=========================================="
echo "AdEzy - MySQL to Supabase Migration"
echo "=========================================="
echo ""

# Step 1: Backup current MySQL data
echo "Step 1: Backing up MySQL data..."
python manage.py dumpdata --natural-foreign --natural-primary --exclude=contenttypes --exclude=auth.Permission > mysql_backup_$(date +%Y%m%d_%H%M%S).json
echo "✓ Backup created successfully"
echo ""

# Step 2: Install PostgreSQL driver
echo "Step 2: Installing PostgreSQL driver..."
pip install psycopg2-binary
echo "✓ Driver installed"
echo ""

# Step 3: Instructions
echo "Step 3: Configure Supabase"
echo "----------------------------------------"
echo "Please complete these steps:"
echo ""
echo "1. Go to https://supabase.com and create a new project"
echo "2. Wait for project creation (2-3 minutes)"
echo "3. Go to Project Settings → Database"
echo "4. Copy your connection details"
echo ""
echo "5. Create a .env file with:"
echo "   USE_SUPABASE=True"
echo "   SUPABASE_DB_HOST=db.xxxxx.supabase.co"
echo "   SUPABASE_DB_NAME=postgres"
echo "   SUPABASE_DB_USER=postgres"
echo "   SUPABASE_DB_PASSWORD=your_password"
echo "   SUPABASE_DB_PORT=5432"
echo ""
read -p "Press Enter after you've configured .env file..."

# Step 4: Run migrations
echo ""
echo "Step 4: Creating database tables in Supabase..."
python manage.py makemigrations
python manage.py migrate
echo "✓ Tables created"
echo ""

# Step 5: Create superuser
echo "Step 5: Creating superuser..."
echo "Please create a superuser account:"
python manage.py createsuperuser
echo "✓ Superuser created"
echo ""

# Step 6: Import data
echo "Step 6: Importing data to Supabase..."
BACKUP_FILE=$(ls -t mysql_backup_*.json | head -1)
python manage.py loaddata "$BACKUP_FILE"
echo "✓ Data imported"
echo ""

echo "=========================================="
echo "Migration Complete! 🎉"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test your application: python manage.py runserver"
echo "2. Verify all data migrated correctly"
echo "3. Check admin panel: http://127.0.0.1:8000/admin"
echo ""
echo "Your MySQL backup is saved as: $BACKUP_FILE"
