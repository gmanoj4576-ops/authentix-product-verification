import os
import uuid
import random
import string
import qrcode
from PIL import Image, ImageDraw, ImageFont
import werkzeug.security as security
from config import Config

def generate_product_id():
    """Generates unique product ID like AUTH-2026-XXXXX"""
    rand_suffix = ''.join(random.choices(string.digits, k=5))
    return f"AUTH-2026-{rand_suffix}"

def generate_verification_code():
    """Generates random 12-char formatted verification code like X7K9-P4M2-Q8T6"""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" # Exclude confusing O, 0, I, 1
    p1 = ''.join(random.choices(chars, k=4))
    p2 = ''.join(random.choices(chars, k=4))
    p3 = ''.join(random.choices(chars, k=4))
    return f"{p1}-{p2}-{p3}"

def generate_qr_reference():
    """Generates unique QR reference token"""
    return f"ref-{uuid.uuid4().hex[:16]}"

def hash_verification_code(code):
    """Hashes verification code using werkzeug/bcrypt security"""
    normalized = code.strip().upper()
    return security.generate_password_hash(normalized, method='pbkdf2:sha256')

def verify_code_hash(submitted_code, stored_hash):
    """Secure comparison of submitted verification code with stored hash"""
    if not submitted_code or not stored_hash:
        return False
    normalized = submitted_code.strip().upper()
    try:
        return security.check_password_hash(stored_hash, normalized)
    except Exception as e:
        print(f"Hash check error: {e}")
        return False

def generate_qr_image(qr_reference, domain_url="http://localhost:5000"):
    """
    Generates QR code PNG image encoding ONLY the verification URL.
    Example URL encoded in QR: http://localhost:5000/verify?t=ref-a8b2c3d4e5f67890
    CRITICAL: Verification Code is NEVER encoded in the QR.
    """
    os.makedirs(Config.QR_FOLDER, exist_ok=True)
    
    verify_url = f"{domain_url.rstrip('/')}/verify?t={qr_reference}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    
    # Generate stylish dark Navy & Cyan accent QR image
    img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert('RGB')
    
    filename = f"{qr_reference}.png"
    filepath = os.path.join(Config.QR_FOLDER, filename)
    img.save(filepath)
    
    return f"/static/qrcodes/{filename}", verify_url
