import os
import sys

try:
    import psycopg2
    from psycopg2 import pool
    PSYCOPG2_AVAILABLE = True
except ImportError as e:
    PSYCOPG2_AVAILABLE = False
    print("="*40)
    print("CRITICAL ERROR: psycopg2 is not installed or importable.")
    print(f"Exception details: {e}")
    print(f"Active Python Interpreter: {sys.executable}")
    print("="*40)

# Retrieve connection string from Render environment or local setup
DATABASE_URL = os.getenv("DATABASE_URL")

db_pool = None

def init_connection_pool():
    global db_pool
    if not DATABASE_URL:
        print("WARNING: DATABASE_URL not set. PostgreSQL connection pool disabled.")
        return False
        
    if not PSYCOPG2_AVAILABLE:
        print("WARNING: psycopg2 not available. PostgreSQL features disabled.")
        return False
        
    try:
        if not db_pool:
            db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)
            print("Successfully connected to PostgreSQL connection pool.")
        return True
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize database connection pool: {e}")
        db_pool = None
        return False

# Initialize pool immediately on import if URL exists
init_connection_pool()

def get_db_connection():
    if not db_pool:
        raise Exception("Database pool is not initialized. Ensure DATABASE_URL is set correctly.")
    return db_pool.getconn()

def release_db_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)
