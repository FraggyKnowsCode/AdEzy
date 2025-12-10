# Supabase Migration Guide for AdEzy

## What is Supabase?
Supabase is an open-source Firebase alternative that provides:
- PostgreSQL database (more powerful than MySQL)
- Real-time subscriptions
- Authentication
- Storage
- Auto-generated APIs

## Step 1: Create Supabase Account & Project

1. Go to https://supabase.com
2. Sign up for a free account
3. Click "New Project"
4. Fill in:
   - Project Name: `adezy` (or any name you prefer)
   - Database Password: Choose a strong password (SAVE THIS!)
   - Region: Choose closest to you
   - Pricing Plan: Free tier is fine for development

5. Wait 2-3 minutes for project to be created

## Step 2: Get Database Credentials

After project creation:
1. Go to Project Settings (gear icon in sidebar)
2. Click "Database" section
3. Scroll to "Connection string" section
4. Copy the "URI" connection string (should look like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```

**Important Connection Details:**
- Host: `db.xxxxx.supabase.co`
- Database: `postgres`
- User: `postgres`
- Password: [Your database password]
- Port: `5432`

## Step 3: Install PostgreSQL Driver

Run this command:
```bash
pip install psycopg2-binary
```

## Step 4: Export Your Current MySQL Data

### Option A: Using Django dumpdata (Recommended)
```bash
python manage.py dumpdata --natural-foreign --natural-primary --exclude=contenttypes --exclude=auth.Permission > data_backup.json
```

### Option B: Manual MySQL Export
```bash
mysqldump -u root adezy_db > adezy_backup.sql
```

## Step 5: Update Django Settings

Your settings.py will be updated to use PostgreSQL/Supabase instead of MySQL.

## Step 6: Run Migrations on Supabase

```bash
# Create new database tables
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Step 7: Import Your Data

```bash
python manage.py loaddata data_backup.json
```

## Benefits of Supabase over MySQL:
✅ **Better Performance**: PostgreSQL is more powerful
✅ **Cloud Hosted**: No need to run XAMPP
✅ **Free Tier**: 500MB database, unlimited API requests
✅ **Auto Backups**: Daily backups included
✅ **Real-time Features**: Built-in subscriptions
✅ **Better JSON Support**: Native JSON columns
✅ **PostGIS Support**: Geographic data if needed
✅ **Connection Pooling**: Better for production

## Troubleshooting

### If migrations fail:
```bash
python manage.py migrate --run-syncdb
```

### If data import fails:
- Import in smaller chunks
- Check for constraint violations
- Ensure all foreign keys exist

### Connection Issues:
- Check your database password
- Verify host URL is correct
- Ensure you're using port 5432
- Check if your IP is whitelisted (Supabase free tier allows all IPs by default)

## Next Steps After Migration:
1. Test all functionality
2. Verify all data migrated correctly
3. Update any raw SQL queries (PostgreSQL syntax slightly different)
4. Consider using Supabase's real-time features
5. Use Supabase Storage for media files instead of local storage

## Need Help?
- Supabase Docs: https://supabase.com/docs
- Django + Supabase: https://supabase.com/docs/guides/integrations/django
