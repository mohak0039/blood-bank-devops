from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models.db import execute_query

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        rows = execute_query('SELECT * FROM users WHERE email = %s', (email,))
        if rows and check_password_hash(rows[0]['password_hash'], password):
            session['user_id'] = rows[0]['id']
            session['user_name'] = rows[0]['name']
            flash(f"Welcome back, {rows[0]['name']}!", 'success')
            return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/admin-login', methods=['POST'])
def admin_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if (username == current_app.config['ADMIN_USERNAME'] and
            password == current_app.config['ADMIN_PASSWORD']):
        session['admin_logged_in'] = True
        session['admin_username'] = username
        flash('Welcome back, Admin!', 'success')
        return redirect(url_for('dashboard'))
    flash('Invalid admin credentials.', 'danger')
    return redirect(url_for('auth.login'))


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
    flash('You have been signed out.', 'info')
    return redirect(url_for('home'))


@auth_bp.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('home'))
