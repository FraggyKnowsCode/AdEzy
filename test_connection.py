import os
import psycopg2
from dotenv import load_dotenv
import socket

load_dotenv()

# Get IPv4 address for the hostname
hostname = os.getenv('SUPABASE_DB_HOST')
print(f"Resolving hostname: {hostname}")

try:
    # Try to get IPv4 address
    result = socket.getaddrinfo(hostname, None, socket.AF_INET)
    if result:
        ipv4_address = result[0][4][0]
        print(f"Found IPv4 address: {ipv4_address}")
        host_to_use = ipv4_address
    else:
        print("No IPv4 address found, using hostname")
        host_to_use = hostname
except socket.gaierror:
    print("Could not resolve to IPv4, trying hostname directly")
    host_to_use = hostname

# Try connection
print(f"\nAttempting connection to: {host_to_use}")
try:
    conn = psycopg2.connect(
        host=host_to_use,
        port=os.getenv('SUPABASE_DB_PORT'),
        database=os.getenv('SUPABASE_DB_NAME'),
        user=os.getenv('SUPABASE_DB_USER'),
        password=os.getenv('SUPABASE_DB_PASSWORD'),
        sslmode='require',
        connect_timeout=10
    )
    print("✓ Connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0]}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Connection failed: {e}")
