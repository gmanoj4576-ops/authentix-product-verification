import os
import random
from datetime import datetime, timedelta
import werkzeug.security as security
import database.db as db
from services.qr_service import (
    generate_verification_code,
    generate_qr_reference,
    hash_verification_code,
    generate_qr_image
)
from ml.anomaly_detector import calculate_product_risk

SAMPLE_PRODUCTS = [
    {
        "product_id": "AUTH-2026-00001",
        "product_name": "[DEMO] Premium Herbal Shampoo",
        "brand": "Botanica Essence",
        "category": "Personal Care",
        "manufacturer": "BioFlora Labs Inc.",
        "batch_number": "BATCH-2026-X89",
        "manufacturing_date": "2026-01-15",
        "expiry_date": "2028-01-15",
        "description": "Organic herbal clarifying shampoo with natural botanical extracts.",
        "image_url": "https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?auto=format&fit=crop&w=600&q=80",
        "status": "Active"
    },
    {
        "product_id": "AUTH-2026-00002",
        "product_name": "[DEMO] Pure Organic Honey",
        "brand": "Valley Gold",
        "category": "Food & Beverage",
        "manufacturer": "Highland Apiaries Co.",
        "batch_number": "HONEY-8820",
        "manufacturing_date": "2026-02-10",
        "expiry_date": "2029-02-10",
        "description": "100% raw unpasteurized wild forest honey.",
        "image_url": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=600&q=80",
        "status": "Active"
    },
    {
        "product_id": "AUTH-2026-00003",
        "product_name": "[DEMO] UltraFit Pro Sports Shoes",
        "brand": "AeroStride",
        "category": "Footwear",
        "manufacturer": "AeroStride Athletics Ltd.",
        "batch_number": "RUN-2026-04",
        "manufacturing_date": "2026-03-01",
        "expiry_date": "2031-03-01",
        "description": "High-performance carbon-plated road running footwear.",
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80",
        "status": "Active"
    },
    {
        "product_id": "AUTH-2026-00004",
        "product_name": "[DEMO] Titanium Smart Watch Ultra",
        "brand": "Kronos Tech",
        "category": "Electronics",
        "manufacturer": "Kronos Innovation Labs",
        "batch_number": "SWU-99401",
        "manufacturing_date": "2026-01-20",
        "expiry_date": "2030-01-20",
        "description": "Rugged GPS smart watch with AMOLED display & biometric sensors.",
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80",
        "status": "Active"
    },
    {
        "product_id": "AUTH-2026-00005",
        "product_name": "[DEMO] Lumina Hydra Face Cream",
        "brand": "DermaPure",
        "category": "Cosmetics",
        "manufacturer": "DermaPure Pharmacal",
        "batch_number": "HYDRA-5512",
        "manufacturing_date": "2026-02-01",
        "expiry_date": "2027-08-01",
        "description": "Intense hydration night cream with hyaluronic acid & niacinamide.",
        "image_url": "https://images.unsplash.com/photo-1608248597261-833244675b16?auto=format&fit=crop&w=600&q=80",
        "status": "Active"
    },
    {
        "product_id": "AUTH-2026-00006",
        "product_name": "[DEMO] Artisan Dark Packaged Coffee",
        "brand": "Summit Roast",
        "category": "Food & Beverage",
        "manufacturer": "Summit Specialty Roasters",
        "batch_number": "ROAST-1049",
        "manufacturing_date": "2026-03-15",
        "expiry_date": "2027-03-15",
        "description": "Single-origin Arabica dark roast whole coffee beans.",
        "image_url": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?auto=format&fit=crop&w=600&q=80",
        "status": "Active"
    },
    {
        "product_id": "AUTH-2026-00007",
        "product_name": "[DEMO] Ayurvedic Hair Growth Oil",
        "brand": "VedaCare",
        "category": "Personal Care",
        "manufacturer": "VedaCare Herbals",
        "batch_number": "OIL-7721",
        "manufacturing_date": "2026-01-10",
        "expiry_date": "2028-01-10",
        "description": "Traditional cold-pressed coconut & bhringraj hair nourishing oil.",
        "image_url": "https://images.unsplash.com/photo-1608248597261-833244675b16?auto=format&fit=crop&w=600&q=80",
        "status": "Active"
    },
    {
        "product_id": "AUTH-2026-00008",
        "product_name": "[DEMO] 65W GaN Fast Charger",
        "brand": "VoltPulse",
        "category": "Electronics",
        "manufacturer": "VoltPulse Electronics",
        "batch_number": "GAN-65W-2026",
        "manufacturing_date": "2025-11-10",
        "expiry_date": "2030-11-10",
        "description": "Ultra-compact dual USB-C Power Delivery wall charger.",
        "image_url": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=600&q=80",
        "status": "Disabled"  # One sample disabled product
    },
    {
        "product_id": "AUTH-2026-00009",
        "product_name": "[DEMO] Himalayan Silver Needle Tea",
        "brand": "Zen Leaf",
        "category": "Food & Beverage",
        "manufacturer": "Zen Leaf Estates",
        "batch_number": "TEA-2024-EX",
        "manufacturing_date": "2024-01-01",
        "expiry_date": "2025-06-01",
        "description": "Rare hand-picked white tea leaves.",
        "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&q=80",
        "status": "Expired"  # One sample expired product
    },
    {
        "product_id": "AUTH-2026-00010",
        "product_name": "[DEMO] Charcoal Detox Organic Soap",
        "brand": "NatureScent",
        "category": "Personal Care",
        "manufacturer": "NatureScent Soapworks",
        "batch_number": "SOAP-9901",
        "manufacturing_date": "2026-02-20",
        "expiry_date": "2028-02-20",
        "description": "Activated bamboo charcoal exfoliating artisan bath soap bar.",
        "image_url": "https://images.unsplash.com/photo-1607006482172-3ba7493a52c3?auto=format&fit=crop&w=600&q=80",
        "status": "Active"
    }
]

def seed_database():
    print("[AUTHENTIX Seed] Initializing database...")
    db.init_db()

    # 1. Create Default Admin
    admin_email = "admin@authentix.com"
    admin_pass = "admin123"
    pass_hash = security.generate_password_hash(admin_pass, method='pbkdf2:sha256')
    db.create_admin(admin_email, pass_hash)
    print(f"[AUTHENTIX Seed] Default Admin created: {admin_email} / {admin_pass}")

    # 2. Seed Products
    seeded_products = []
    print("[AUTHENTIX Seed] Registering 10 sample products with QR codes & codes...")

    for i, prod in enumerate(SAMPLE_PRODUCTS):
        existing = db.get_product_by_id(prod['product_id'])
        if existing:
            seeded_products.append((existing, "X7K9-P4M2-Q8T6")) # Default code fallback
            continue

        ver_code = generate_verification_code()
        qr_ref = generate_qr_reference()
        code_hash = hash_verification_code(ver_code)
        qr_img_path, _ = generate_qr_image(qr_ref)

        product_record = {
            "product_id": prod['product_id'],
            "product_name": prod['product_name'],
            "brand": prod['brand'],
            "category": prod['category'],
            "manufacturer": prod['manufacturer'],
            "batch_number": prod['batch_number'],
            "manufacturing_date": prod['manufacturing_date'],
            "expiry_date": prod['expiry_date'],
            "description": prod['description'],
            "image_url": prod['image_url'],
            "qr_reference": qr_ref,
            "verification_code_hash": code_hash,
            "status": prod['status']
        }

        db.create_product(product_record)
        seeded_products.append((product_record, ver_code))
        print(f" -> Product registered: {prod['product_id']} | Code: {ver_code} | Ref: {qr_ref}")

    # 3. Seed Realistic Verification History Logs for AI Analytics & Chart.js Demo
    print("[AUTHENTIX Seed] Generating historical verification logs for AI telemetry...")
    
    devices = [
        "iPhone 15 Pro / Safari 17.4",
        "Samsung Galaxy S24 / Chrome 122",
        "Google Pixel 8 / Chrome 121",
        "MacBook Pro / Chrome 123",
        "iPad Pro / Mobile Safari 17.2",
        "Unknown Mobile Device / Android WebKit"
    ]

    now = datetime.now()

    # Product 1 (Herbal Shampoo): Normal usage - mostly verified
    p1_id = SAMPLE_PRODUCTS[0]['product_id']
    for i in range(12):
        delta = timedelta(days=random.randint(0, 5), hours=random.randint(1, 10))
        ts = (now - delta).strftime("%Y-%m-%d %H:%M:%S")
        db.log_verification(p1_id, "VERIFIED", "", random.choice(devices), "web_camera", risk_score=10.0)

    # Product 2 (Honey): HIGH RISK / SUSPICIOUS DEMO PRODUCT
    # Multiple failed attempts from different devices within short timeframe
    p2_id = SAMPLE_PRODUCTS[1]['product_id']
    for i in range(8):
        ts = (now - timedelta(minutes=random.randint(5, 45))).strftime("%Y-%m-%d %H:%M:%S")
        db.log_verification(
            p2_id, 
            "INCORRECT_CODE", 
            "Submitted verification code did not match product records", 
            random.choice(devices), 
            "web_camera", 
            risk_score=75.0
        )
    # Add suspicious tag
    db.log_verification(p2_id, "SUSPICIOUS", "High failed attempt frequency detected", devices[0], "web_camera", risk_score=85.0)

    # Product 3 (Sports Shoes): Mixed verification history
    p3_id = SAMPLE_PRODUCTS[2]['product_id']
    for i in range(6):
        db.log_verification(p3_id, "VERIFIED", "", devices[1], "web_camera", risk_score=15.0)
    db.log_verification(p3_id, "INCORRECT_CODE", "Typo in verification code", devices[2], "web_camera", risk_score=25.0)

    # Calculate and store initial AI Risk Scores for all products
    for prod in SAMPLE_PRODUCTS:
        p_id = prod['product_id']
        risk_res = calculate_product_risk(p_id)
        db.save_risk_analysis(p_id, risk_res['risk_score'], risk_res['risk_level'], risk_res['reason'], risk_res['model_version'])

    print("[AUTHENTIX Seed] Database seed completed successfully!")

if __name__ == '__main__':
    seed_database()
