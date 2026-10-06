import os
import sqlite3
from datetime import datetime
from config import Config

# Supabase Client Import safely
supabase_client = None
if Config.SUPABASE_URL and Config.SUPABASE_KEY and not Config.SUPABASE_URL.startswith("https://your-supabase"):
    try:
        from supabase import create_client
        supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    except Exception as e:
        print(f"[AUTHENTIX DB Warning] Could not initialize Supabase client: {e}")

def get_sqlite_conn():
    os.makedirs(os.path.dirname(Config.SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes local SQLite schema if needed and creates tables."""
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            brand TEXT NOT NULL,
            category TEXT NOT NULL,
            manufacturer TEXT,
            batch_number TEXT NOT NULL,
            manufacturing_date TEXT,
            expiry_date TEXT,
            description TEXT,
            image_url TEXT,
            qr_reference TEXT UNIQUE NOT NULL,
            verification_code_hash TEXT NOT NULL,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Verification logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            verification_status TEXT NOT NULL,
            failure_reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            device_information TEXT,
            verification_source TEXT DEFAULT 'web_camera',
            risk_score REAL DEFAULT 0.0
        )
    ''')
    
    # Admins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Risk analysis table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            risk_score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            reason TEXT,
            model_version TEXT DEFAULT 'v1.0-isolation-forest',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Audit logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_email TEXT,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# --- Product Data Functions ---

def get_product_by_ref(qr_reference):
    if supabase_client:
        try:
            res = supabase_client.table('products').select('*').eq('qr_reference', qr_reference).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            print(f"Supabase error, falling back to SQLite: {e}")
            
    conn = get_sqlite_conn()
    row = conn.execute("SELECT * FROM products WHERE qr_reference = ?", (qr_reference,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_product_by_id(product_id):
    if supabase_client:
        try:
            res = supabase_client.table('products').select('*').eq('product_id', product_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            print(f"Supabase error: {e}")

    conn = get_sqlite_conn()
    row = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_products(search=None, category=None, status=None, sort_by='created_at', order='DESC'):
    conn = get_sqlite_conn()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if search:
        query += " AND (product_name LIKE ? OR brand LIKE ? OR product_id LIKE ? OR batch_number LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
    if category and category != 'All':
        query += " AND category = ?"
        params.append(category)
    if status and status != 'All':
        query += " AND status = ?"
        params.append(status)
        
    valid_sorts = ['created_at', 'product_name', 'brand', 'category', 'status', 'product_id']
    if sort_by not in valid_sorts:
        sort_by = 'created_at'
    if order.upper() not in ['ASC', 'DESC']:
        order = 'DESC'
        
    query += f" ORDER BY {sort_by} {order}"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_product(data):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT OR IGNORE INTO products (
            product_id, product_name, brand, category, manufacturer, 
            batch_number, manufacturing_date, expiry_date, description, 
            image_url, qr_reference, verification_code_hash, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['product_id'], data['product_name'], data['brand'], data['category'],
        data.get('manufacturer', ''), data['batch_number'], data.get('manufacturing_date', ''),
        data.get('expiry_date', ''), data.get('description', ''), data.get('image_url', ''),
        data['qr_reference'], data['verification_code_hash'], data.get('status', 'Active'), now, now
    ))
    conn.commit()
    conn.close()
    
    if supabase_client:
        try:
            supabase_client.table('products').insert(data).execute()
        except Exception as e:
            print(f"Supabase insert error: {e}")

def update_product_status(product_id, new_status):
    conn = get_sqlite_conn()
    conn.execute("UPDATE products SET status = ?, updated_at = ? WHERE product_id = ?",
                 (new_status, datetime.now().isoformat(), product_id))
    conn.commit()
    conn.close()

# --- Verification Logs Functions ---

def log_verification(product_id, status, failure_reason="", device_info="Browser", source="web_camera", risk_score=0.0):
    conn = get_sqlite_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute('''
        INSERT INTO verification_logs (product_id, verification_status, failure_reason, timestamp, device_information, verification_source, risk_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (product_id, status, failure_reason, now, device_info, source, risk_score))
    conn.commit()
    conn.close()
    
    if supabase_client:
        try:
            supabase_client.table('verification_logs').insert({
                'product_id': product_id,
                'verification_status': status,
                'failure_reason': failure_reason,
                'timestamp': now,
                'device_information': device_info,
                'verification_source': source,
                'risk_score': risk_score
            }).execute()
        except Exception as e:
            print(f"Supabase log verification error: {e}")

def get_verification_logs(product_id=None, limit=100):
    conn = get_sqlite_conn()
    if product_id:
        rows = conn.execute("SELECT * FROM verification_logs WHERE product_id = ? ORDER BY id DESC LIMIT ?", (product_id, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM verification_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_logs_with_product_details(limit=200):
    conn = get_sqlite_conn()
    query = '''
        SELECT v.*, p.product_name, p.brand, p.category, p.batch_number
        FROM verification_logs v
        LEFT JOIN products p ON v.product_id = p.product_id
        ORDER BY v.id DESC LIMIT ?
    '''
    rows = conn.execute(query, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Admin & Auth Functions ---

def get_admin_by_email(email):
    conn = get_sqlite_conn()
    row = conn.execute("SELECT * FROM admins WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_admin(email, password_hash):
    conn = get_sqlite_conn()
    conn.execute("INSERT OR IGNORE INTO admins (email, password_hash) VALUES (?, ?)", (email, password_hash))
    conn.commit()
    conn.close()

# --- Risk & Intelligence Functions ---

def save_risk_analysis(product_id, risk_score, risk_level, reason, model_version='v1.0-isolation-forest'):
    conn = get_sqlite_conn()
    conn.execute('''
        INSERT INTO risk_analysis (product_id, risk_score, risk_level, reason, model_version)
        VALUES (?, ?, ?, ?, ?)
    ''', (product_id, risk_score, risk_level, reason, model_version))
    conn.commit()
    conn.close()

def get_latest_risk_analysis(product_id):
    conn = get_sqlite_conn()
    row = conn.execute("SELECT * FROM risk_analysis WHERE product_id = ? ORDER BY id DESC LIMIT 1", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def log_audit(admin_email, action, details=""):
    conn = get_sqlite_conn()
    conn.execute("INSERT INTO audit_logs (admin_email, action, details) VALUES (?, ?, ?)", (admin_email, action, details))
    conn.commit()
    conn.close()

def get_dashboard_summary():
    conn = get_sqlite_conn()
    total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_verifications = conn.execute("SELECT COUNT(*) FROM verification_logs").fetchone()[0]
    successful_verifications = conn.execute("SELECT COUNT(*) FROM verification_logs WHERE verification_status = 'VERIFIED'").fetchone()[0]
    failed_verifications = conn.execute("SELECT COUNT(*) FROM verification_logs WHERE verification_status IN ('INCORRECT_CODE', 'INVALID_REFERENCE')").fetchone()[0]
    suspicious_verifications = conn.execute("SELECT COUNT(*) FROM verification_logs WHERE verification_status = 'SUSPICIOUS'").fetchone()[0]
    
    conn.close()
    return {
        'total_products': total_products,
        'total_verifications': total_verifications,
        'successful_verifications': successful_verifications,
        'failed_verifications': failed_verifications,
        'suspicious_verifications': suspicious_verifications
    }
