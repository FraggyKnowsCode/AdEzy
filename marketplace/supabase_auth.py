"""
Supabase Authentication Integration for AdEzy
Connects Django user registration, login, and profile updates directly
with Supabase's auth.users and auth.identities tables.
"""
import json
import uuid
import logging
from django.db import connection
from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

def is_supabase_enabled():
    return getattr(settings, 'USE_SUPABASE', False)

def create_or_update_supabase_auth_user(email, password, username=None, display_name=None):
    """
    Creates or updates a user in Supabase auth.users and auth.identities tables.
    Returns (success, error_message, user_id)
    """
    if not is_supabase_enabled():
        return True, None, None

    try:
        with connection.cursor() as cur:
            # Check if user already exists in auth.users by email
            cur.execute("SELECT id FROM auth.users WHERE email = %s;", (email,))
            row = cur.fetchone()
            
            metadata = {'username': username or email.split('@')[0]}
            if display_name:
                metadata['name'] = display_name
            metadata_json = json.dumps(metadata)

            if row:
                user_id = row[0]
                if password:
                    cur.execute("""
                        UPDATE auth.users
                        SET encrypted_password = crypt(%s, gen_salt('bf')),
                            raw_user_meta_data = %s::jsonb,
                            updated_at = now()
                        WHERE id = %s;
                    """, (password, metadata_json, user_id))
                else:
                    cur.execute("""
                        UPDATE auth.users
                        SET raw_user_meta_data = %s::jsonb,
                            updated_at = now()
                        WHERE id = %s;
                    """, (metadata_json, user_id))
                return True, None, user_id
            else:
                user_id = str(uuid.uuid4())
                # 1. Insert into auth.users
                cur.execute("""
                    INSERT INTO auth.users (
                        instance_id, id, aud, role, email, encrypted_password,
                        email_confirmed_at, recovery_sent_at, last_sign_in_at,
                        raw_app_meta_data, raw_user_meta_data, created_at, updated_at,
                        confirmation_token, email_change, email_change_token_new, recovery_token
                    ) VALUES (
                        '00000000-0000-0000-0000-000000000000',
                        %s,
                        'authenticated',
                        'authenticated',
                        %s,
                        crypt(%s, gen_salt('bf')),
                        now(), now(), now(),
                        '{"provider":"email","providers":["email"]}'::jsonb,
                        %s::jsonb,
                        now(), now(),
                        '', '', '', ''
                    );
                """, (user_id, email, password, metadata_json))

                # 2. Insert into auth.identities
                identity_data = json.dumps({'sub': user_id, 'email': email, 'email_verified': True})
                cur.execute("""
                    INSERT INTO auth.identities (
                        id, user_id, identity_data, provider, provider_id, last_sign_in_at, created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(),
                        %s,
                        %s::jsonb,
                        'email',
                        %s,
                        now(), now(), now()
                    );
                """, (user_id, identity_data, user_id))

                return True, None, user_id
    except Exception as e:
        logger.error(f"Error creating/updating Supabase auth user: {e}")
        return False, str(e), None

def update_supabase_password(email, new_password):
    """
    Updates the password for a user in Supabase auth.users.
    """
    if not is_supabase_enabled():
        return True, None

    try:
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE auth.users
                SET encrypted_password = crypt(%s, gen_salt('bf')),
                    updated_at = now()
                WHERE email = %s;
            """, (new_password, email))
            return True, None
    except Exception as e:
        logger.error(f"Error updating Supabase password: {e}")
        return False, str(e)

def verify_supabase_user(email_or_username, password):
    """
    Verifies user credentials against Supabase auth.users.
    Returns (user_obj_or_None, error_message)
    """
    if not is_supabase_enabled():
        return None, "Supabase is not enabled"

    try:
        # Determine email
        if '@' in email_or_username:
            user = User.objects.filter(email=email_or_username).first()
            email = email_or_username
        else:
            user = User.objects.filter(username=email_or_username).first()
            email = user.email if user else f"{email_or_username}@adezy.com"

        if not email:
            return None, "User not found"

        with connection.cursor() as cur:
            cur.execute("""
                SELECT id, email FROM auth.users 
                WHERE email = %s AND encrypted_password = crypt(%s, encrypted_password);
            """, (email, password))
            row = cur.fetchone()
            if row:
                # Update last_sign_in_at
                cur.execute("UPDATE auth.users SET last_sign_in_at = now() WHERE id = %s;", (row[0],))
                return user, None
            else:
                return None, "Invalid credentials"
    except Exception as e:
        logger.error(f"Error verifying Supabase user: {e}")
        return None, str(e)
