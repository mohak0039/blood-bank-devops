from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models.db import execute_query

auth_bp = Blueprint('auth', __name__)


def _is_safe_url(target):
    if not target:
        return False
    parsed = urlparse(target)
    return not parsed.netloc and not parsed.scheme


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        rows = execute_query('SELECT * FROM users WHERE email = %s', (email,))
        if rows and check_password_hash(rows[0]['password_hash'], password):
            user = rows[0]
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            if user.get('is_admin'):
                session['admin_logged_in'] = True
                session['admin_username'] = user['name']
            flash(f"Welcome back, {user['name']}!", 'success')
            next_url = request.args.get('next')
            return redirect(next_url if _is_safe_url(next_url) else url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html'), 400

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html'), 400

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register.html'), 400

        existing = execute_query('SELECT id FROM users WHERE email = %s', (email,))
        if existing:
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register.html'), 400

        pw_hash = generate_password_hash(password)
        user_id = execute_query(
            'INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)',
            (name, email, pw_hash),
            fetch=False,
        )
        session['user_id'] = user_id
        session['user_name'] = name
        flash(f'Account created! Welcome, {name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('You have been signed out.', 'info')
    return redirect(url_for('home'))


@auth_bp.route('/admin-logout')
def admin_logout():
    return redirect(url_for('auth.logout'))
