from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import database.db as db
from services.verification_service import process_verification

verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/verify', methods=['GET'])
def verify_page():
    qr_ref = request.args.get('t', '').strip()
    
    if not qr_ref:
        # Show general scan / enter reference page
        return render_template('verify.html', product=None, qr_reference="")

    product = db.get_product_by_ref(qr_ref)
    
    if not product:
        # Record invalid attempt and render invalid result screen
        result = process_verification(qr_ref, "", device_info=request.user_agent.string, source="web_url")
        return render_template('result_invalid.html', result=result)

    if product.get('status') == 'Disabled':
        result = process_verification(qr_ref, "", device_info=request.user_agent.string, source="web_url")
        return render_template('result_disabled.html', product=product, result=result)

    if product.get('status') == 'Expired':
        result = process_verification(qr_ref, "", device_info=request.user_agent.string, source="web_url")
        return render_template('result_expired.html', product=product, result=result)

    # Valid product found: render verification page with basic product info and code prompt
    return render_template('verify.html', product=product, qr_reference=qr_ref)

@verification_bp.route('/verify/submit', methods=['POST'])
def submit_verification_code():
    qr_ref = request.form.get('qr_reference', '').strip()
    code = request.form.get('verification_code', '').strip()
    device_info = request.user_agent.string or "Browser Scanner"

    result = process_verification(qr_ref, code, device_info=device_info, source="web_form")

    if result['status'] == 'VERIFIED':
        return render_template('result_genuine.html', result=result)
    elif result['status'] == 'INCORRECT_CODE':
        return render_template('result_counterfeit.html', result=result)
    elif result['status'] == 'DISABLED':
        return render_template('result_disabled.html', product=result.get('product'), result=result)
    elif result['status'] == 'EXPIRED':
        return render_template('result_expired.html', product=result.get('product'), result=result)
    else:
        return render_template('result_invalid.html', result=result)

# --- API Endpoints ---

@verification_bp.route('/api/verify/<reference>', methods=['GET'])
def api_verify_reference(reference):
    product = db.get_product_by_ref(reference)
    if not product:
        return jsonify({
            'success': False,
            'status': 'INVALID_REFERENCE',
            'message': 'Product reference not found'
        }), 404

    # Return only basic public info (never expose verification code hash or internal keys)
    return jsonify({
        'success': True,
        'status': product.get('status', 'Active'),
        'product': {
            'product_id': product['product_id'],
            'product_name': product['product_name'],
            'brand': product['brand'],
            'category': product['category'],
            'image_url': product.get('image_url', ''),
            'batch_number': product['batch_number']
        }
    })

@verification_bp.route('/api/verify/code', methods=['POST'])
def api_verify_code():
    data = request.get_json() or {}
    qr_ref = data.get('qr_reference', '').strip()
    code = data.get('verification_code', '').strip()
    device_info = data.get('device_info', request.user_agent.string or "API Client")

    if not qr_ref or not code:
        return jsonify({'error': 'Missing qr_reference or verification_code'}), 400

    result = process_verification(qr_ref, code, device_info=device_info, source="api")
    return jsonify(result)
