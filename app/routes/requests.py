from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.db import (
    add_inventory_history,
    approve_blood_request,
    create_blood_request,
    get_all_blood_requests,
    get_blood_inventory_by_type,
    get_blood_request_by_id,
    get_hospitals_list,
    get_user_blood_requests,
    reject_blood_request,
    update_blood_units,
)
from utils import login_required, user_login_required

requests_bp = Blueprint('requests', __name__)

BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


@requests_bp.route('/')
@user_login_required
def list_requests():
    if session.get('admin_logged_in'):
        blood_requests = get_all_blood_requests()
    else:
        blood_requests = get_user_blood_requests(session.get('user_id'))
    return render_template('requests/list.html', blood_requests=blood_requests)


@requests_bp.route('/new', methods=['GET', 'POST'])
@user_login_required
def new_request():
    hospitals = get_hospitals_list()

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

        create_blood_request(
            session.get('user_id'), patient_name, blood_type, int(units_required),
            hospital or None, hospital_id, contact_phone, urgency,
        )
        flash(f'Blood request for {patient_name} submitted!', 'success')
        return redirect(url_for('requests.list_requests'))

    return render_template('requests/new.html', blood_types=BLOOD_TYPES, hospitals=hospitals)


@requests_bp.route('/approve/<int:request_id>', methods=['POST'])
@login_required
def approve(request_id):
    req = get_blood_request_by_id(request_id)
    if not req:
        flash('Request not found.', 'danger')
        return redirect(url_for('requests.list_requests'))

    item = get_blood_inventory_by_type(req['blood_type'])
    if not item or item['units'] < req['units_required']:
        flash(f'Insufficient {req["blood_type"]} units in inventory.', 'danger')
        return redirect(url_for('requests.list_requests'))

    new_units = item['units'] - req['units_required']
    update_blood_units(req['blood_type'], new_units)
    add_inventory_history(
        req['blood_type'], -req['units_required'], new_units,
        f'Request #{request_id} approved',
    )
    approve_blood_request(request_id, datetime.now())
    flash(f'Request #{request_id} approved. Inventory updated.', 'success')
    return redirect(url_for('requests.list_requests'))


@requests_bp.route('/reject/<int:request_id>', methods=['POST'])
@login_required
def reject(request_id):
    reject_blood_request(request_id, datetime.now())
    flash(f'Request #{request_id} rejected.', 'warning')
    return redirect(url_for('requests.list_requests'))
