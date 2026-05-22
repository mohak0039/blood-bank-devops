from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.db import execute_query
from utils import login_required, user_login_required

requests_bp = Blueprint('requests', __name__)

BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


@requests_bp.route('/')
@user_login_required
def list_requests():
    user_id = session.get('user_id')
    if session.get('admin_logged_in') or not user_id:
        blood_requests = execute_query('SELECT * FROM blood_requests ORDER BY requested_at DESC')
    else:
        blood_requests = execute_query(
            'SELECT * FROM blood_requests WHERE user_id = %s ORDER BY requested_at DESC',
            (user_id,),
        )
    return render_template('requests/list.html', blood_requests=blood_requests)


@requests_bp.route('/new', methods=['GET', 'POST'])
@user_login_required
def new_request():
    hospitals = execute_query('SELECT id, name FROM hospitals ORDER BY name')

    if request.method == 'POST':
        patient_name = request.form.get('patient_name', '').strip()
        blood_type = request.form.get('blood_type', '').strip()
        units_required = request.form.get('units_required', '').strip()
        hospital = request.form.get('hospital', '').strip()
        hospital_id = request.form.get('hospital_id') or None
        contact_phone = request.form.get('contact_phone', '').strip()
        urgency = request.form.get('urgency', 'normal')

        if not patient_name or not blood_type or not units_required or not contact_phone:
            flash('Patient name, blood type, units, and phone are required.', 'danger')
            return render_template('requests/new.html', blood_types=BLOOD_TYPES, hospitals=hospitals), 400

        execute_query(
            '''INSERT INTO blood_requests
               (user_id, patient_name, blood_type, units_required, hospital, hospital_id,
                contact_phone, urgency)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (session.get('user_id'), patient_name, blood_type, int(units_required),
             hospital or None, hospital_id, contact_phone, urgency),
            fetch=False,
        )
        flash(f'Blood request for {patient_name} submitted!', 'success')
        return redirect(url_for('requests.list_requests'))

    return render_template('requests/new.html', blood_types=BLOOD_TYPES, hospitals=hospitals)


@requests_bp.route('/approve/<int:request_id>', methods=['POST'])
@login_required
def approve(request_id):
    rows = execute_query('SELECT * FROM blood_requests WHERE id = %s', (request_id,))
    if not rows:
        flash('Request not found.', 'danger')
        return redirect(url_for('requests.list_requests'))

    req = rows[0]
    inventory = execute_query('SELECT * FROM blood_inventory WHERE blood_type = %s', (req['blood_type'],))

    if not inventory or inventory[0]['units'] < req['units_required']:
        flash(f'Insufficient {req["blood_type"]} units in inventory.', 'danger')
        return redirect(url_for('requests.list_requests'))

    new_units = inventory[0]['units'] - req['units_required']
    execute_query(
        'UPDATE blood_inventory SET units = %s WHERE blood_type = %s',
        (new_units, req['blood_type']), fetch=False,
    )
    execute_query(
        'INSERT INTO inventory_history (blood_type, change_amount, units_after, reason) VALUES (%s, %s, %s, %s)',
        (req['blood_type'], -req['units_required'], new_units, f'Request #{request_id} approved'),
        fetch=False,
    )
    execute_query(
        "UPDATE blood_requests SET status='approved', resolved_at=%s WHERE id=%s",
        (datetime.now(), request_id), fetch=False,
    )
    flash(f'Request #{request_id} approved. Inventory updated.', 'success')
    return redirect(url_for('requests.list_requests'))


@requests_bp.route('/reject/<int:request_id>', methods=['POST'])
@login_required
def reject(request_id):
    execute_query(
        "UPDATE blood_requests SET status='rejected', resolved_at=%s WHERE id=%s",
        (datetime.now(), request_id), fetch=False,
    )
    flash(f'Request #{request_id} rejected.', 'warning')
    return redirect(url_for('requests.list_requests'))
