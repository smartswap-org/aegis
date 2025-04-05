import pytest
from run import app
from api.database import get_db
from api.utils.auth import generate_token

@pytest.fixture(autouse=True)
def cleanup():
    db = get_db()
    if db:
        cursor = db.cursor()
        cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
        cursor.execute('DELETE FROM app')
        cursor.execute('DELETE FROM cex_market')
        cursor.execute('DELETE FROM funds')
        cursor.execute('DELETE FROM wallets_access')
        cursor.execute('DELETE FROM bots')
        cursor.execute('DELETE FROM wallets')
        cursor.execute('DELETE FROM clients')
        cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
        db.commit()
        cursor.close()
        db.close()
    yield

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_token(client):
    register_data = {
        'user': 'testuser',
        'password': 'testpassword',
        'power': 1
    }
    register_response = client.post('/api/auth/register', json=register_data)
    if register_response.status_code not in [201, 400]:  # 400 means user already exists
        pytest.fail(f"Failed to register user: {register_response.data}")
    
    login_data = {
        'user': 'testuser',
        'password': 'testpassword'
    }
    login_response = client.post('/api/auth/login', json=login_data)
    if login_response.status_code != 200:
        pytest.fail(f"Failed to login: {login_response.data}")
    
    token = login_response.json.get('token')
    if not token:
        pytest.fail("No token received from login")
    return token

@pytest.fixture
def test_wallet(client, auth_token):
    data = {
        'name': 'testwallet',
        'address': '0x123',
        'keys': {'private': 'key1', 'public': 'key2'}
    }
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.post('/api/wallets/', json=data, headers=headers)
    if response.status_code not in [201, 400]:
        pytest.fail(f"Failed to create wallet: {response.data}")
    return 'testwallet'

@pytest.fixture
def test_bot(client, auth_token, test_wallet):
    data = {
        'name': 'testbot',
        'exchange_name': 'Binance',
        'pairs': '["BTC/USDC"]',
        'strategy': 'test_strategy',
        'reinvest_gains': True,
        'position_percent_invest': 50.00,
        'invest_capital': 1000.00,
        'adjust_with_profits_if_loss': True,
        'timeframe': '1h',
        'simulation': True
    }
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.post('/api/bots/', json=data, headers=headers)
    if response.status_code != 201:
        pytest.fail(f"Failed to create bot: {response.data}")
    return data['name']

@pytest.mark.run(order=1)
def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"AEGIS API Documentation" in response.data

@pytest.mark.run(order=2)
def test_register(client):
    data = {
        'user': 'newuser',
        'password': 'testpassword'
    }
    response = client.post('/api/auth/register', json=data)
    assert response.status_code in [201, 400]

@pytest.mark.run(order=3)
def test_login(client):
    data = {
        'user': 'testuser',
        'password': 'testpassword'
    }
    response = client.post('/api/auth/login', json=data)
    assert response.status_code in [200, 401]

@pytest.mark.run(order=4)
def test_logout(client):
    response = client.post('/api/auth/logout')
    assert response.status_code == 200

@pytest.mark.run(order=5)
def test_create_wallet(client, auth_token):
    data = {
        'name': 'new_testwallet',
        'address': '0x123',
        'keys': {'private': 'key1', 'public': 'key2'}
    }
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.post('/api/wallets/', json=data, headers=headers)
    assert response.status_code in [201, 400]

@pytest.mark.run(order=6)
def test_get_wallet(client, auth_token, test_wallet):
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.get(f'/api/wallets/{test_wallet}', headers=headers)
    assert response.status_code in [200, 403, 404]

@pytest.mark.run(order=7)
def test_create_position(client, auth_token, test_bot):
    data = {
        'buy_order_id': 123456,
        'buy_price': 100.0,
        'buy_quantity': 1.0,
        'buy_fees': 0.1,
        'buy_value_usdc': 100.0,
        'exchange': 'binance',
        'pair': 'BTC/USDC',
        'bot_name': test_bot
    }
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.post('/api/positions/', json=data, headers=headers)
    assert response.status_code == 201

@pytest.mark.run(order=8)
def test_get_positions(client, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.get('/api/positions/', headers=headers)
    assert response.status_code == 200

@pytest.mark.run(order=9)
def test_get_position(client, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.get('/api/positions/1', headers=headers)
    assert response.status_code in [200, 404]

@pytest.mark.run(order=10)
def test_create_fund(client, auth_token, test_bot):
    data = {
        'bot_name': test_bot,
        'funds': 1000.0
    }
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.post('/api/funds/', json=data, headers=headers)
    assert response.status_code == 201

@pytest.mark.run(order=11)
def test_get_funds(client, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.get('/api/funds/', headers=headers)
    assert response.status_code == 200

@pytest.mark.run(order=12)
def test_get_fund(client, auth_token, test_bot):
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.get(f'/api/funds/{test_bot}', headers=headers)
    assert response.status_code in [200, 404]

@pytest.mark.run(order=13)
def test_delete_wallet(client, auth_token, test_wallet):
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.delete(f'/api/wallets/{test_wallet}', headers=headers)
    assert response.status_code in [200, 403, 404] 