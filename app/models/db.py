import mysql.connector
from flask import current_app


def get_connection():
    return mysql.connector.connect(
        host=current_app.config['DB_HOST'],
        user=current_app.config['DB_USER'],
        password=current_app.config['DB_PASSWORD'],
        database=current_app.config['DB_NAME'],
    )


def execute_query(query, params=None, fetch=True):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    if fetch:
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    else:
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return last_id


# --- Blood Requests ---

def get_all_blood_requests():
    return execute_query('SELECT * FROM blood_requests ORDER BY requested_at DESC')


def get_user_blood_requests(user_id):
    return execute_query(
        'SELECT * FROM blood_requests WHERE user_id = %s ORDER BY requested_at DESC',
        (user_id,),
    )


def get_blood_request_by_id(request_id):
    rows = execute_query('SELECT * FROM blood_requests WHERE id = %s', (request_id,))
    return rows[0] if rows else None


def create_blood_request(user_id, patient_name, blood_type, units_required,
                         hospital, hospital_id, contact_phone, urgency):
    return execute_query(
        '''INSERT INTO blood_requests
           (user_id, patient_name, blood_type, units_required, hospital, hospital_id,
            contact_phone, urgency)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
        (user_id, patient_name, blood_type, units_required,
         hospital, hospital_id, contact_phone, urgency),
        fetch=False,
    )


def approve_blood_request(request_id, resolved_at):
    execute_query(
        "UPDATE blood_requests SET status='approved', resolved_at=%s WHERE id=%s",
        (resolved_at, request_id), fetch=False,
    )


def reject_blood_request(request_id, resolved_at):
    execute_query(
        "UPDATE blood_requests SET status='rejected', resolved_at=%s WHERE id=%s",
        (resolved_at, request_id), fetch=False,
    )


# --- Blood Inventory ---

def get_blood_inventory_by_type(blood_type):
    rows = execute_query('SELECT * FROM blood_inventory WHERE blood_type = %s', (blood_type,))
    return rows[0] if rows else None


def update_blood_units(blood_type, units):
    execute_query(
        'UPDATE blood_inventory SET units = %s WHERE blood_type = %s',
        (units, blood_type), fetch=False,
    )


def add_inventory_history(blood_type, change_amount, units_after, reason):
    execute_query(
        'INSERT INTO inventory_history (blood_type, change_amount, units_after, reason) '
        'VALUES (%s, %s, %s, %s)',
        (blood_type, change_amount, units_after, reason),
        fetch=False,
    )


# --- Hospitals ---

def get_all_hospitals():
    return execute_query('SELECT * FROM hospitals ORDER BY name')


def get_hospitals_list():
    return execute_query('SELECT id, name FROM hospitals ORDER BY name')


def create_hospital(name, address, phone, email, city):
    execute_query(
        'INSERT INTO hospitals (name, address, phone, email, city) VALUES (%s, %s, %s, %s, %s)',
        (name, address or None, phone, email or None, city or None),
        fetch=False,
    )


def delete_hospital(hospital_id):
    rows = execute_query('SELECT id FROM hospitals WHERE id = %s', (hospital_id,))
    if not rows:
        return False
    execute_query('DELETE FROM hospitals WHERE id = %s', (hospital_id,), fetch=False)
    return True


# --- Donors ---

def get_approved_donors(blood_type=None):
    base = "SELECT * FROM donors WHERE status='approved'"
    if blood_type:
        return execute_query(base + ' AND blood_type = %s ORDER BY name', (blood_type,))
    return execute_query(base + ' ORDER BY name')


def get_pending_donors():
    return execute_query("SELECT * FROM donors WHERE status='pending' ORDER BY created_at DESC")


def get_donor_by_id(donor_id):
    rows = execute_query('SELECT * FROM donors WHERE id = %s', (donor_id,))
    return rows[0] if rows else None


def insert_donor(name, age, blood_type, phone, email, city, last_donated):
    return execute_query(
        '''INSERT INTO donors (name, age, blood_type, phone, email, city, last_donated, status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')''',
        (name, age, blood_type, phone, email, city, last_donated),
        fetch=False,
    )


def update_donor_status(donor_id, status):
    execute_query('UPDATE donors SET status=%s WHERE id=%s', (status, donor_id), fetch=False)


def remove_donor(donor_id):
    execute_query('DELETE FROM donors WHERE id=%s', (donor_id,), fetch=False)
