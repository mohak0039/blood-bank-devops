from flask import Blueprint, flash, redirect, render_template, request, url_for

from models.db import execute_query
from utils import login_required

inventory_bp = Blueprint('inventory', __name__)

BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


@inventory_bp.route('/')
def list_inventory():
    inventory = execute_query('SELECT * FROM blood_inventory ORDER BY blood_type')
    return render_template('inventory/list.html', inventory=inventory)


@inventory_bp.route('/update/<blood_type>', methods=['GET', 'POST'])
@login_required
def update(blood_type):
    if blood_type not in BLOOD_TYPES:
        flash(f'Invalid blood type. Allowed: {", ".join(BLOOD_TYPES)}', 'danger')
        return redirect(url_for('inventory.list_inventory'))

    rows = execute_query('SELECT * FROM blood_inventory WHERE blood_type = %s', (blood_type,))
    if not rows:
        flash(f'Blood type {blood_type} not found.', 'danger')
        return redirect(url_for('inventory.list_inventory'))

    item = rows[0]

    if request.method == 'POST':
        action = request.form.get('action', 'add')
        amount = int(request.form.get('amount', 0))

        if action == 'add':
            new_units = item['units'] + amount
            change = amount
        else:
            new_units = max(0, item['units'] - amount)
            change = -(item['units'] - new_units)
            if abs(change) < amount:
                flash(
                    f'Warning: Only {abs(change)} units removed '
                    f'(requested {amount}). Insufficient stock.',
                    'warning',
                )

        execute_query(
            'UPDATE blood_inventory SET units = %s WHERE blood_type = %s',
            (new_units, blood_type),
            fetch=False,
        )
        execute_query(
            'INSERT INTO inventory_history (blood_type, change_amount, units_after, reason) '
            'VALUES (%s, %s, %s, %s)',
            (blood_type, change, new_units, 'Manual update'),
            fetch=False,
        )
        if action == 'add' or abs(change) == amount:
            flash(f'{blood_type} inventory updated to {new_units} units.', 'success')
        return redirect(url_for('inventory.list_inventory'))

    return render_template('inventory/update.html', item=item)


@inventory_bp.route('/history')
def history():
    blood_type = request.args.get('blood_type', 'A+')
    if blood_type not in BLOOD_TYPES:
        flash(f'Invalid blood type. Allowed: {", ".join(BLOOD_TYPES)}', 'danger')
        return redirect(url_for('inventory.list_inventory'))
    records = execute_query(
        'SELECT * FROM inventory_history WHERE blood_type = %s ORDER BY recorded_at DESC LIMIT 30',
        (blood_type,),
    )
    labels = [str(r['recorded_at']) for r in reversed(records)]
    data = [r['units_after'] for r in reversed(records)]
    return render_template(
        'inventory/history.html',
        blood_type=blood_type,
        blood_types=BLOOD_TYPES,
        records=records,
        labels=labels,
        data=data,
    )
