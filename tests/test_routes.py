import pytest
from conftest import app
from api.database import get_db
from api.utils.auth import generate_token

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers():
    token = generate_token({'user': 'testuser'})
    return {'Authorization': f'Bearer {token}'}

def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"AEGIS API Documentation" in response.data

def test_register(client):
    data = {
        'user': 'testuser',
        'password': 'testpassword'
    }
    response = client.post('/api/auth/register', json=data)
    assert response.status_code in [201, 400]

def test_login(client):
    data = {
        'user': 'testuser',
        'password': 'testpassword'
    }
    response = client.post('/api/auth/login', json=data)
    assert response.status_code in [200, 401]

def test_logout(client):
    response = client.post('/api/auth/logout')
    assert response.status_code == 200

def test_create_position(client):
    data = {
        'buy_order_id': 123456,
        'buy_price': 100.0,
        'buy_quantity': 1.0,
        'buy_fees': 0.1,
        'buy_value_usdt': 100.0,
        'exchange': 'binance',
        'pair': 'BTC/USDT',
        'bot_name': 'testbot'
    }
    response = client.post('/api/positions/', json=data)
    assert response.status_code == 201

def test_get_positions(client):
    response = client.get('/api/positions/')
    assert response.status_code == 200

def test_get_position(client):
    response = client.get('/api/positions/1')
    assert response.status_code in [200, 404]

def test_create_fund(client):
    data = {
        'bot_name': 'testbot',
        'funds': 1000.0
    }
    response = client.post('/api/funds/', json=data)
    assert response.status_code == 201

def test_get_funds(client):
    response = client.get('/api/funds/')
    assert response.status_code == 200

def test_get_fund(client):
    response = client.get('/api/funds/testbot')
    assert response.status_code in [200, 404]

def test_create_wallet(client, auth_headers):
    data = {
        'name': 'testwallet',
        'address': '0x123456789',
        'keys': {
            'private_key': 'test_private_key',
            'public_key': 'test_public_key'
        }
    }
    response = client.post('/api/wallets/', json=data, headers=auth_headers)
    assert response.status_code in [201, 400]

def test_get_wallet(client, auth_headers):
    response = client.get('/api/wallets/testwallet', headers=auth_headers)
    assert response.status_code in [200, 404]

def test_delete_wallet(client, auth_headers):
    response = client.delete('/api/wallets/testwallet', headers=auth_headers)
    assert response.status_code in [200, 404] 