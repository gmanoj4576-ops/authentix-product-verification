import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'authentix-super-secret-key-2026-default')
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
    PORT = int(os.getenv('PORT', 5050))
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # SQLite Database path & QR storage (Supports Vercel serverless /tmp directory)
    if os.getenv('VERCEL'):
        SQLITE_DB_PATH = '/tmp/authentix.db'
        STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
        QR_FOLDER = '/tmp/qrcodes'
    else:
        SQLITE_DB_PATH = os.path.join(BASE_DIR, 'database', 'authentix.db')
        STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
        QR_FOLDER = os.path.join(STATIC_FOLDER, 'qrcodes')
    
    # Rate Limiting configuration
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
