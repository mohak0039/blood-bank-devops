from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.db import (
    get_approved_donors,
    get_donor_by_id,
    get_pending_donors,
    insert_donor,
    remove_donor,
    update_donor_status,
)
from utils import donor_eligibility, login_required, user_login_required

donors_bp = Blueprint('donors', __name__)

BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


@donors_bp.route('/')
def list_donors():
    blood_type = request.args.get('blood_type', '')
    is_admin = session.get('admin_logged_in', False)

    donors = get_approved_donors(blood_type or None)
    for d in donors:
        d['eligibility'] = donor_eligibility(d.get('last_donated'))

    pending = get_pending_donors() if is_admin else []

    return render_template(
        'donors/list.html',
        donors=donors,
        pending=pending,
        blood_types=BLOOD_TYPES,
        selected=blood_type,
    )


@donors_bp.route('/register', methods=['GET', 'POST'])
@user_login_required
def register():
    if session.get('admin_logged_in'):
        flash('Admin accounts cannot apply as donors.', 'warning')
        return redirect(url_for('donors.list_donors'))

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

        insert_donor(name, int(age), blood_type, phone, email or None, city or None, last_donated)
        flash('Your donor application has been submitted and is awaiting admin approval.', 'success')
        return redirect(url_for('donors.list_donors'))

    return render_template('donors/register.html', blood_types=BLOOD_TYPES)


@donors_bp.route('/<int:donor_id>/approve', methods=['POST'])
@login_required
def approve_donor(donor_id):
    donor = get_donor_by_id(donor_id)
    if not donor:
        flash('Donor not found.', 'danger')
        return redirect(url_for('donors.list_donors'))
    if donor['status'] != 'pending':
        flash('Donor is not in pending status.', 'warning')
        return redirect(url_for('donors.list_donors'))
    update_donor_status(donor_id, 'approved')
    flash('Donor application approved.', 'success')
    return redirect(url_for('donors.list_donors'))


@donors_bp.route('/<int:donor_id>/reject', methods=['POST'])
@login_required
def reject_donor(donor_id):
    donor = get_donor_by_id(donor_id)
    if not donor:
        flash('Donor not found.', 'danger')
        return redirect(url_for('donors.list_donors'))
    if donor['status'] != 'pending':
        flash('Donor is not in pending status.', 'warning')
        return redirect(url_for('donors.list_donors'))
    update_donor_status(donor_id, 'rejected')
    flash('Donor application rejected.', 'warning')
    return redirect(url_for('donors.list_donors'))


@donors_bp.route('/<int:donor_id>/delete', methods=['POST'])
@login_required
def delete_donor(donor_id):
    donor = get_donor_by_id(donor_id)
    if not donor:
        flash('Donor not found.', 'danger')
        return redirect(url_for('donors.list_donors'))
    remove_donor(donor_id)
    flash('Donor removed.', 'success')
    return redirect(url_for('donors.list_donors'))


@donors_bp.route('/<int:donor_id>')
def detail(donor_id):
    donor = get_donor_by_id(donor_id)
    if not donor:
        return render_template('404.html'), 404
    donor['eligibility'] = donor_eligibility(donor.get('last_donated'))
    return render_template('donors/detail.html', donor=donor)
