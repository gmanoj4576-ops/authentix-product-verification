# AUTHENTIX
### AI-Based Fake Product Detection & Product Authentication System
**Tagline: Verify Before You Trust**

AUTHENTIX is a full-stack cybersecurity and product verification platform designed to eliminate counterfeit products using dual-factor QR code separation and AI-driven suspicious activity analysis.

---

## Key Features

1. **Dual-Factor Separation**:
   - **QR Reference**: Encodes ONLY a unique reference URL (e.g. `https://domain/verify?t=ref-xxx`). The QR code **NEVER** contains the Verification Code.
   - **Verification Code**: A random 12-character secret code (e.g. `X7K9-P4M2-Q8T6`) printed separately on physical packaging. Stored as a secure salted hash (`bcrypt`/`pbkdf2`) in the database.
2. **Public Customer Verification Page (`/verify`)**:
   - Web camera QR scanner & QR image upload.
   - Basic product information lookup.
   - Verification Code entry & secure comparison.
   - Animated visual result screens (**GENUINE PRODUCT**, **POSSIBLE COUNTERFEIT**, **INVALID PRODUCT**, **PRODUCT VERIFICATION UNAVAILABLE**, **PRODUCT EXPIRED**).
3. **Manufacturer Admin Dashboard (`/admin/dashboard`)**:
   - Protected admin authentication & session management.
   - Product catalog management (Search, filter by category/status, sort, pagination).
   - Instant QR generation & download PNG.
   - Dedicated printable packaging QR label format.
4. **AI Verification Intelligence (`/admin/ai-intelligence`)**:
   - Machine Learning Anomaly Detection using `scikit-learn` `IsolationForest` combined with transparent heuristic rule scoring.
   - Analyzes verification frequency, failure rate, distinct device counts, and scan velocity.
   - Dynamic visual dashboards using **Chart.js**.
   - Product Authentication Intelligence detail view (`/admin/products/<id>/intelligence`).
5. **Audit Trail & CSV Export**:
   - Detailed log of every verification attempt.
   - Export verification history as CSV for compliance.

---

## Technology Stack

- **Frontend**: HTML5, Vanilla CSS (Cyber Dark Navy Glassmorphism Theme), JavaScript, Bootstrap 5, Chart.js, HTML5-QRCode.
- **Backend**: Python 3.9+, Flask framework, Flask-CORS, Werkzeug security.
- **Database**: Supabase PostgreSQL (Supports local SQLite automatic fallback for instant zero-config setup).
- **AI & Anomaly Detection**: scikit-learn (`IsolationForest`), pandas, NumPy.
- **QR Generation**: Python `qrcode` library & Pillow.

---

## Database Schema

- `products`: id, product_id, product_name, brand, category, manufacturer, batch_number, manufacturing_date, expiry_date, description, image_url, qr_reference, verification_code_hash, status, created_at, updated_at
- `verification_logs`: id, product_id, verification_status, failure_reason, timestamp, device_information, verification_source, risk_score
- `admins`: id, email, password_hash, created_at
- `risk_analysis`: id, product_id, risk_score, risk_level, reason, model_version, created_at
- `audit_logs`: id, admin_email, action, details, timestamp

---

## Quick Start (Running Locally)

1. Activate virtual environment and install dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

2. (Optional) Configure environment variables in `.env`:
```text
SECRET_KEY=authentix-secret-key-2026
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
PORT=5000
```

3. Launch the application:
```bash
python3 app.py
```

4. Open browser at `http://localhost:5000`:
   - Landing Page: `http://localhost:5000/`
   - Customer Verify: `http://localhost:5000/verify`
   - Admin Login: `http://localhost:5000/admin/login`
     - **Email**: `admin@authentix.com`
     - **Password**: `admin123`

---

## API Endpoints

- `POST /api/admin/login`: Authenticate administrator
- `POST /api/products`: Register new product & generate QR
- `GET /api/products`: List registered products
- `GET /api/products/<id>`: Get product details
- `GET /api/products/<id>/history`: Get product verification log history
- `GET /api/verify/<reference>`: Lookup product by QR reference
- `POST /api/verify/code`: Submit verification code for verification check
- `GET /api/dashboard/stats`: Get dashboard statistics
- `GET /api/ai/risk/<product_id>`: Get AI risk score for specific product
- `POST /api/ai/analyze`: Trigger full system AI anomaly analysis

---

## Verification Testing Workflow

1. Register a new product in Admin Dashboard -> Receives Product ID, Verification Code, and QR Reference.
2. Scan QR or visit `/verify?t=<reference>` -> Only basic product info is displayed.
3. Enter correct Verification Code -> Displays **✓ GENUINE PRODUCT**.
4. Enter incorrect Verification Code -> Displays **⚠ POSSIBLE COUNTERFEIT** and logs failure.
5. Enter invalid reference -> Displays **⚠ INVALID PRODUCT**.
