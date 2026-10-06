from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from functools import wraps
import werkzeug.security as security
import database.db as db

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized admin access required'}), 401
            return redirect(url_for('auth.admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('products.admin_dashboard'))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()
        else:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()

        admin = db.get_admin_by_email(email)
        
        if admin and security.check_password_hash(admin['password_hash'], password):
            session['admin_logged_in'] = True
            session['admin_email'] = admin['email']
            db.log_audit(admin['email'], 'ADMIN_LOGIN', 'Successful administrator authentication')
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('products.admin_dashboard')})
            return redirect(url_for('products.admin_dashboard'))

        error_msg = 'Invalid credentials. Access denied.'
        db.log_audit(email, 'ADMIN_LOGIN_FAILED', 'Failed login attempt')

        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 401

        return render_template('admin/login.html', error=error_msg)

    return render_template('admin/login.html')

@auth_bp.route('/admin/logout', methods=['GET', 'POST'])
def admin_logout():
    email = session.get('admin_email', 'unknown')
    db.log_audit(email, 'ADMIN_LOGOUT', 'Administrator logged out')
    session.clear()
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    return redirect(url_for('auth.admin_login'))

@auth_bp.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    return admin_login()
