from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
import os
from config import Config
from database.db import init_db
from database.seed import seed_database
from routes.auth import auth_bp
from routes.products import products_bp
from routes.verification import verification_bp
from routes.analytics import analytics_bp

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)

    # Enable CORS
    CORS(app)

    # Initialize SQLite / Supabase tables & auto-seed if empty
    init_db()
    seed_database()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(verification_bp)
    app.register_blueprint(analytics_bp)

    # Landing Page Route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Serve QR images dynamically from /tmp/qrcodes or static/qrcodes
    @app.route('/static/qrcodes/<filename>')
    def serve_qr(filename):
        file_path = os.path.join(Config.QR_FOLDER, filename)
        if os.path.exists(file_path):
            return send_from_directory(Config.QR_FOLDER, filename)
        static_qr = os.path.join(Config.STATIC_FOLDER, 'qrcodes', filename)
        if os.path.exists(static_qr):
            return send_from_directory(os.path.join(Config.STATIC_FOLDER, 'qrcodes'), filename)
        return "QR Code not found", 404

    # Error Handlers (never expose internal tracebacks to customers)
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', code=404, title="PAGE NOT FOUND", 
                               message="The requested resource or product verification route does not exist."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', code=500, title="SYSTEM UNAVAILABLE", 
                               message="An unexpected security system error occurred. Please try again later."), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)
