import pytest


SAMPLE_DONOR = {
    'id': 1, 'name': 'Rahul Singh', 'age': 28, 'blood_type': 'O+',
    'phone': '9876543210', 'email': 'rahul@example.com',
    'city': 'Delhi', 'last_donated': None, 'created_at': '2024-01-01',
}


def test_donor_list_page_loads(client, mocker):
    mocker.patch('routes.donors.get_approved_donors', return_value=[SAMPLE_DONOR])
    response = client.get('/donors/')
    assert response.status_code == 200
    assert b'Rahul Singh' in response.data


def test_register_form_loads(client):
    response = client.get('/donors/register')
    assert response.status_code == 200
    assert b'Register New Donor' in response.data


def test_register_donor_valid_data(client, mocker):
    mocker.patch('models.db.execute_query', return_value=1)
    response = client.post('/donors/register', data={
        'name': 'Priya Sharma',
        'age': '25',
        'blood_type': 'A+',
        'phone': '9123456789',
        'email': 'priya@example.com',
        'city': 'Mumbai',
        'last_donated': '',
    })
    assert response.status_code == 302


def test_register_donor_missing_required_fields(client):
    response = client.post('/donors/register', data={
        'name': '',
        'age': '',
        'blood_type': '',
        'phone': '',
    })
    assert response.status_code == 400
