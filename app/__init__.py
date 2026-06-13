import sys

from flask import Flask, render_template, request, session
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash

from config import config_map
from models.db import execute_query

csrf = CSRFProtect()

_WEAK_ADMIN_DEFAULTS = {'admin', 'admin123', ''}


def ensure_schema(app):
    """Create any missing tables/columns for existing databases."""
    if app.config.get('TESTING'):
        return
    with app.app_context():
        try:
            execute_query('''
                CREATE TABLE IF NOT EXISTS users (
                    id            INT AUTO_INCREMENT PRIMARY KEY,
                    name          VARCHAR(100) NOT NULL,
                    email         VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''', fetch=False)

            execute_query('''
                CREATE TABLE IF NOT EXISTS hospitals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    address VARCHAR(255),
                    phone VARCHAR(15) NOT NULL,
                    email VARCHAR(100),
                    city VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''', fetch=False)

            execute_query('''
                CREATE TABLE IF NOT EXISTS inventory_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    blood_type VARCHAR(5) NOT NULL,
                    change_amount INT NOT NULL,
                    units_after INT NOT NULL,
                    reason VARCHAR(150),
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''', fetch=False)

            donor_cols = execute_query('''
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'donors'
            ''')
            donor_col_names = [c['COLUMN_NAME'] for c in donor_cols]
            if 'status' not in donor_col_names:
                execute_query(
                    "ALTER TABLE donors ADD COLUMN status ENUM('pending','approved','rejected') DEFAULT 'approved'",
                    fetch=False,
                )

            cols = execute_query('''
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'blood_requests'
            ''')
            col_names = [c['COLUMN_NAME'] for c in cols]

            if 'contact_email' not in col_names:
                execute_query(
                    'ALTER TABLE blood_requests ADD COLUMN contact_email VARCHAR(100)',
                    fetch=False,
                )
            if 'hospital_id' not in col_names:
                execute_query(
                    'ALTER TABLE blood_requests ADD COLUMN hospital_id INT NULL',
                    fetch=False,
                )
            if 'user_id' not in col_names:
                execute_query(
                    'ALTER TABLE blood_requests ADD COLUMN user_id INT NULL',
                    fetch=False,
                )

            user_cols = execute_query('''
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'
            ''')
            user_col_names = [c['COLUMN_NAME'] for c in user_cols]
            if 'is_admin' not in user_col_names:
                execute_query(
                    'ALTER TABLE users ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0',
                    fetch=False,
                )
        except Exception as e:
            app.logger.error(f'Schema migration failed: {e}')
            raise


def ensure_admin_user(app):
    """Create or update the admin account in the DB from environment config."""
    if app.config.get('TESTING'):
        return
    admin_email = app.config.get('ADMIN_USERNAME')
    admin_pass = app.config.get('ADMIN_PASSWORD')
    if not admin_email or not admin_pass:
        return
    with app.app_context():
        try:
            pw_hash = generate_password_hash(admin_pass)
            existing = execute_query('SELECT id FROM users WHERE email = %s', (admin_email,))
            if existing:
                execute_query(
                    'UPDATE users SET password_hash = %s, is_admin = 1 WHERE email = %s',
                    (pw_hash, admin_email), fetch=False,
                )
            else:
                execute_query(
                    'INSERT INTO users (name, email, password_hash, is_admin) VALUES (%s, %s, %s, 1)',
                    ('Admin', admin_email, pw_hash), fetch=False,
                )
        except Exception as e:
            app.logger.error(f'Admin user sync failed: {e}')


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    if config_name == 'production':
        admin_user = app.config.get('ADMIN_USERNAME') or ''
        admin_pass = app.config.get('ADMIN_PASSWORD') or ''
        if not admin_user or not admin_pass or admin_user in _WEAK_ADMIN_DEFAULTS or admin_pass in _WEAK_ADMIN_DEFAULTS:
            sys.exit(
                'ERROR: Production requires ADMIN_USERNAME and ADMIN_PASSWORD '
                'env vars set to strong, non-default values.'
            )

    app.config.setdefault('WTF_CSRF_ENABLED', True)
    if app.config.get('TESTING'):
        app.config['WTF_CSRF_ENABLED'] = False
    csrf.init_app(app)

    from routes.auth import auth_bp
    from routes.donors import donors_bp
    from routes.hospitals import hospitals_bp
    from routes.inventory import inventory_bp
    from routes.requests import requests_bp
    from utils import user_login_required

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(donors_bp, url_prefix='/donors')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(requests_bp, url_prefix='/requests')
    app.register_blueprint(hospitals_bp, url_prefix='/hospitals')

    ensure_schema(app)
    ensure_admin_user(app)

    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/dashboard')
    @user_login_required
    def dashboard():
        donor_count = execute_query('SELECT COUNT(*) AS cnt FROM donors')[0]['cnt']
        total_units = execute_query('SELECT COALESCE(SUM(units), 0) AS total FROM blood_inventory')[0]['total']
        pending_count = execute_query(
            "SELECT COUNT(*) AS cnt FROM blood_requests WHERE status='pending'"
        )[0]['cnt']
        hospital_count = execute_query('SELECT COUNT(*) AS cnt FROM hospitals')[0]['cnt']
        low_stock = execute_query(
            'SELECT blood_type, units FROM blood_inventory WHERE units < 5 ORDER BY units'
        )
        inventory = execute_query('SELECT blood_type, units FROM blood_inventory ORDER BY blood_type')
        return render_template(
            'index.html',
            donor_count=donor_count,
            total_units=total_units,
            pending_count=pending_count,
            hospital_count=hospital_count,
            low_stock=low_stock,
            inventory=inventory,
        )

    @app.route('/search')
    def search():
        q = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'donor')
        results = []
        if q:
            if search_type == 'donor':
                results = execute_query(
                    'SELECT * FROM donors WHERE blood_type = %s ORDER BY name', (q,)
                )
            else:
                results = execute_query(
                    'SELECT * FROM blood_inventory WHERE blood_type = %s', (q,)
                )
        return render_template('search.html', results=results, q=q, search_type=search_type)

    return app
