from flask import Blueprint, request, jsonify, render_template, redirect, url_for, send_file, flash, session
import os
import database.db as db
from routes.auth import login_required
from services.qr_service import (
    generate_product_id,
    generate_verification_code,
    generate_qr_reference,
    hash_verification_code,
    generate_qr_image
)
from ml.anomaly_detector import calculate_product_risk
from config import Config

products_bp = Blueprint('products', __name__)

@products_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    stats = db.get_dashboard_summary()
    recent_logs = db.get_logs_with_product_details(limit=10)
    all_products = db.get_all_products()
    
    # Calculate high risk products count
    high_risk_count = 0
    for p in all_products:
        risk = calculate_product_risk(p['product_id'])
        if risk['risk_level'] in ['HIGH', 'CRITICAL']:
            high_risk_count += 1
            
    stats['high_risk_count'] = high_risk_count
    
    return render_template('admin/dashboard.html', stats=stats, recent_logs=recent_logs)

@products_bp.route('/admin/products')
@login_required
def product_list():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', 'All')
    status = request.args.get('status', 'All')
    sort_by = request.args.get('sort_by', 'created_at')
    
    products = db.get_all_products(search=search, category=category, status=status, sort_by=sort_by)
    
    # Enrich product list with risk scores & verification counts
    enriched_products = []
    for p in products:
        p_dict = dict(p)
        logs = db.get_verification_logs(product_id=p['product_id'])
        p_dict['verification_count'] = len(logs)
        risk_data = calculate_product_risk(p['product_id'])
        p_dict['risk_score'] = risk_data['risk_score']
        p_dict['risk_level'] = risk_data['risk_level']
        enriched_products.append(p_dict)

    return render_template(
        'admin/products.html', 
        products=enriched_products, 
        search=search, 
        category=category, 
        status=status, 
        sort_by=sort_by
    )

@products_bp.route('/admin/products/register', methods=['GET', 'POST'])
@login_required
def register_product():
    if request.method == 'POST':
        product_name = request.form.get('product_name', '').strip()
        brand = request.form.get('brand', '').strip()
        category = request.form.get('category', '').strip()
        manufacturer = request.form.get('manufacturer', '').strip()
        batch_number = request.form.get('batch_number', '').strip()
        mfg_date = request.form.get('manufacturing_date', '').strip()
        exp_date = request.form.get('expiry_date', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()

        if not product_name or not brand or not category or not batch_number:
            flash('Product Name, Brand, Category, and Batch Number are required.', 'danger')
            return redirect(url_for('products.register_product'))

        # Step 1: Generate unique Product ID
        product_id = generate_product_id()
        
        # Step 2: Generate random Verification Code
        verification_code = generate_verification_code()
        
        # Step 3: Generate unique QR Reference
        qr_reference = generate_qr_reference()
        
        # Step 4: Hash Verification Code securely
        code_hash = hash_verification_code(verification_code)
        
        # Step 5: Generate QR Image containing ONLY the QR Reference URL
        domain_url = request.host_url
        qr_image_url, encoded_url = generate_qr_image(qr_reference, domain_url=domain_url)

        # Step 6: Store product in database
        product_data = {
            "product_id": product_id,
            "product_name": product_name,
            "brand": brand,
            "category": category,
            "manufacturer": manufacturer,
            "batch_number": batch_number,
            "manufacturing_date": mfg_date,
            "expiry_date": exp_date,
            "description": description,
            "image_url": image_url or 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=600&q=80',
            "qr_reference": qr_reference,
            "verification_code_hash": code_hash,
            "status": "Active"
        }
        
        db.create_product(product_data)
        db.log_audit(session.get('admin_email'), 'PRODUCT_REGISTERED', f"Registered product {product_id} ({product_name})")
        
        # Store registration result in session to display the generated code & QR on confirmation page
        session['last_registered'] = {
            "product": product_data,
            "verification_code": verification_code,
            "qr_image_url": qr_image_url,
            "encoded_url": encoded_url
        }

        return redirect(url_for('products.registration_success'))

    return render_template('admin/register_product.html')

@products_bp.route('/admin/products/success')
@login_required
def registration_success():
    data = session.get('last_registered')
    if not data:
        return redirect(url_for('products.product_list'))
    return render_template('admin/registration_success.html', data=data)

@products_bp.route('/admin/products/<product_id>')
@login_required
def product_detail(product_id):
    product = db.get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('products.product_list'))

    logs = db.get_verification_logs(product_id=product_id, limit=50)
    risk_info = calculate_product_risk(product_id)

    return render_template('admin/product_detail.html', product=product, logs=logs, risk=risk_info)

@products_bp.route('/admin/products/<product_id>/disable', methods=['POST'])
@login_required
def disable_product(product_id):
    product = db.get_product_by_id(product_id)
    if product:
        new_status = 'Disabled' if product['status'] == 'Active' else 'Active'
        db.update_product_status(product_id, new_status)
        db.log_audit(session.get('admin_email'), f'PRODUCT_STATUS_{new_status.upper()}', f"Changed status of {product_id} to {new_status}")
        flash(f"Product status updated to {new_status}.", "success")
    return redirect(url_for('products.product_detail', product_id=product_id))

@products_bp.route('/admin/qr/<product_id>')
@login_required
def qr_display(product_id):
    product = db.get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('products.product_list'))

    qr_image_path = f"/static/qrcodes/{product['qr_reference']}.png"
    domain_url = request.host_url
    encoded_url = f"{domain_url.rstrip('/')}/verify?t={product['qr_reference']}"

    return render_template('admin/qr_display.html', product=product, qr_image_path=qr_image_path, encoded_url=encoded_url)

@products_bp.route('/admin/products/<product_id>/download-qr')
@login_required
def download_qr(product_id):
    product = db.get_product_by_id(product_id)
    if not product:
        return "Product not found", 404

    qr_ref = product['qr_reference']
    file_path = os.path.join(Config.QR_FOLDER, f"{qr_ref}.png")

    if not os.path.exists(file_path):
        # Regenerate if missing
        generate_qr_image(qr_ref, domain_url=request.host_url)

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"AUTHENTIX_QR_{product['product_id']}_{qr_ref}.png"
    )

@products_bp.route('/admin/logs')
@login_required
def verification_logs():
    logs = db.get_logs_with_product_details(limit=200)
    return render_template('admin/logs.html', logs=logs)

# --- API Endpoints ---

@products_bp.route('/api/products', methods=['GET'])
def api_get_products():
    products = db.get_all_products()
    return jsonify({'success': True, 'products': products})

@products_bp.route('/api/products', methods=['POST'])
@login_required
def api_create_product():
    data = request.get_json() or {}
    product_name = data.get('product_name')
    brand = data.get('brand')
    category = data.get('category')
    batch_number = data.get('batch_number')

    if not product_name or not brand or not category or not batch_number:
        return jsonify({'error': 'Missing required product fields'}), 400

    product_id = generate_product_id()
    verification_code = generate_verification_code()
    qr_reference = generate_qr_reference()
    code_hash = hash_verification_code(verification_code)
    qr_image_url, encoded_url = generate_qr_image(qr_reference, domain_url=request.host_url)

    record = {
        "product_id": product_id,
        "product_name": product_name,
        "brand": brand,
        "category": category,
        "manufacturer": data.get('manufacturer', ''),
        "batch_number": batch_number,
        "manufacturing_date": data.get('manufacturing_date', ''),
        "expiry_date": data.get('expiry_date', ''),
        "description": data.get('description', ''),
        "image_url": data.get('image_url', ''),
        "qr_reference": qr_reference,
        "verification_code_hash": code_hash,
        "status": "Active"
    }

    db.create_product(record)

    return jsonify({
        'success': True,
        'product': record,
        'verification_code': verification_code,
        'qr_image_url': qr_image_url,
        'encoded_url': encoded_url
    }), 201

@products_bp.route('/api/products/<product_id>', methods=['GET'])
def api_get_product(product_id):
    product = db.get_product_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'success': True, 'product': product})

@products_bp.route('/api/products/<product_id>/history', methods=['GET'])
def api_get_product_history(product_id):
    logs = db.get_verification_logs(product_id=product_id)
    return jsonify({'success': True, 'product_id': product_id, 'history': logs})
