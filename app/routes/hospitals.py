from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from models.db import create_hospital, delete_hospital, get_all_hospitals
from utils import login_required

hospitals_bp = Blueprint('hospitals', __name__)


@hospitals_bp.route('/')
def list_hospitals():
    hospitals = get_all_hospitals()
    return render_template('hospitals/list.html', hospitals=hospitals)


@hospitals_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        city = request.form.get('city', '').strip()

        if not name or not phone:
            flash('Hospital name and phone are required.', 'danger')
            return render_template('hospitals/register.html'), 400

        try:
            create_hospital(name, address, phone, email, city)
            flash(f'Hospital "{name}" registered successfully!', 'success')
        except Exception as e:
            current_app.logger.error(f'Failed to register hospital: {e}')
            flash('Failed to register hospital. Please try again.', 'danger')
            return render_template('hospitals/register.html'), 500

        return redirect(url_for('hospitals.list_hospitals'))

    return render_template('hospitals/register.html')


@hospitals_bp.route('/delete/<int:hospital_id>', methods=['POST'])
@login_required
def delete(hospital_id):
    if not delete_hospital(hospital_id):
        flash('Hospital not found.', 'danger')
        return redirect(url_for('hospitals.list_hospitals'))
    flash('Hospital removed.', 'info')
    return redirect(url_for('hospitals.list_hospitals'))
