from flask import Blueprint, request, jsonify, render_template, Response, flash, redirect, url_for
import csv
import io
import database.db as db
from routes.auth import login_required
from services.ai_service import get_system_ai_intelligence
from ml.anomaly_detector import calculate_product_risk

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/admin/ai-intelligence')
@login_required
def ai_intelligence_page():
    ai_data = get_system_ai_intelligence()
    return render_template('admin/intelligence.html', ai=ai_data)

@analytics_bp.route('/admin/products/<product_id>/intelligence')
@login_required
def product_intelligence_page(product_id):
    product = db.get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('products.product_list'))

    risk_info = calculate_product_risk(product_id)
    logs = db.get_verification_logs(product_id=product_id, limit=50)

    return render_template('admin/product_intelligence.html', product=product, risk=risk_info, logs=logs)

@analytics_bp.route('/admin/export/logs.csv')
@login_required
def export_logs_csv():
    logs = db.get_logs_with_product_details(limit=1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        'Log ID', 'Product ID', 'Product Name', 'Brand', 'Batch Number', 
        'Verification Status', 'Failure Reason', 'Timestamp', 
        'Risk Score', 'Device Information', 'Source'
    ])
    
    for log in logs:
        risk_level = "LOW"
        score = log.get('risk_score', 0.0)
        if score > 80: risk_level = "CRITICAL"
        elif score > 60: risk_level = "HIGH"
        elif score > 30: risk_level = "MEDIUM"

        writer.writerow([
            log.get('id'),
            log.get('product_id', 'N/A'),
            log.get('product_name', 'Unknown'),
            log.get('brand', 'N/A'),
            log.get('batch_number', 'N/A'),
            log.get('verification_status'),
            log.get('failure_reason', ''),
            log.get('timestamp'),
            f"{score:.1f} ({risk_level})",
            log.get('device_information', ''),
            log.get('verification_source', '')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=AUTHENTIX_Verification_History.csv"}
    )

# --- API Endpoints ---

@analytics_bp.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    summary = db.get_dashboard_summary()
    ai_summary = get_system_ai_intelligence()
    summary['high_risk_count'] = ai_summary['high_risk_count']
    summary['overall_risk_score'] = ai_summary['overall_risk_score']
    return jsonify({'success': True, 'stats': summary})

@analytics_bp.route('/api/ai/risk/<product_id>', methods=['GET'])
def api_product_risk(product_id):
    product = db.get_product_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    risk_info = calculate_product_risk(product_id)
    return jsonify({'success': True, 'risk': risk_info})

@analytics_bp.route('/api/ai/analyze', methods=['POST'])
@login_required
def api_trigger_ai_analysis():
    ai_data = get_system_ai_intelligence()
    db.log_audit(request.headers.get('Admin-Email', 'admin@authentix.com'), 'AI_ANALYSIS_TRIGGERED', 'Full anomaly scan executed')
    return jsonify({'success': True, 'intelligence': ai_data})
