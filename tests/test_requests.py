import pytest


SAMPLE_REQUEST = {
    'id': 1, 'patient_name': 'Anita Patel', 'blood_type': 'B+',
    'units_required': 2, 'hospital': 'City Hospital', 'contact_phone': '9000000001',
    'urgency': 'urgent', 'status': 'pending',
    'requested_at': '2024-01-01', 'resolved_at': None,
}


def test_requests_list_loads(client, mocker):
    mocker.patch('routes.requests.get_user_blood_requests', return_value=[SAMPLE_REQUEST])
    response = client.get('/requests/')
    assert response.status_code == 200
    assert b'Anita Patel' in response.data


def test_new_request_form_loads(client):
    response = client.get('/requests/new')
    assert response.status_code == 200
    assert b'New Blood Request' in response.data


def test_create_request_valid(client, mocker):
    mocker.patch('models.db.execute_query', return_value=1)
    response = client.post('/requests/new', data={
        'patient_name': 'Suresh Kumar',
        'blood_type': 'AB-',
        'units_required': '3',
        'hospital': 'Apollo',
        'contact_phone': '9111111111',
        'urgency': 'normal',
    })
    assert response.status_code == 302


def test_create_request_missing_fields(client):
    response = client.post('/requests/new', data={
        'patient_name': '',
        'blood_type': '',
        'units_required': '',
        'contact_phone': '',
    })
    assert response.status_code == 400
