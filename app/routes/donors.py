from flask import Blueprint, flash, redirect, render_template, request, url_for

from models.db import execute_query
from utils import login_required, user_login_required, donor_eligibility

donors_bp = Blueprint('donors', __name__)

BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


@donors_bp.route('/')
def list_donors():
    blood_type = request.args.get('blood_type', '')
    if blood_type:
        donors = execute_query(
            'SELECT * FROM donors WHERE blood_type = %s ORDER BY name', (blood_type,)
        )
    else:
        donors = execute_query('SELECT * FROM donors ORDER BY name')

    for d in donors:
        d['eligibility'] = donor_eligibility(d.get('last_donated'))

    return render_template('donors/list.html', donors=donors, blood_types=BLOOD_TYPES, selected=blood_type)


@donors_bp.route('/register', methods=['GET', 'POST'])
@user_login_required
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '').strip()
        blood_type = request.form.get('blood_type', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        city = request.form.get('city', '').strip()
        last_donated = request.form.get('last_donated') or None

        if not name or not age or not blood_type or not phone:
            flash('Name, age, blood type, and phone are required.', 'danger')
            return render_template('donors/register.html', blood_types=BLOOD_TYPES), 400

        execute_query(
            '''INSERT INTO donors (name, age, blood_type, phone, email, city, last_donated)
               VALUES (%s, %s, %s, %s, %s, %s, %s)''',
            (name, int(age), blood_type, phone, email or None, city or None, last_donated),
            fetch=False,
        )
        flash(f'Donor {name} registered successfully!', 'success')
        return redirect(url_for('donors.list_donors'))

    return render_template('donors/register.html', blood_types=BLOOD_TYPES)


@donors_bp.route('/<int:donor_id>')
def detail(donor_id):
    rows = execute_query('SELECT * FROM donors WHERE id = %s', (donor_id,))
    if not rows:
        return render_template('404.html'), 404
    donor = rows[0]
    donor['eligibility'] = donor_eligibility(donor.get('last_donated'))
    return render_template('donors/detail.html', donor=donor)
