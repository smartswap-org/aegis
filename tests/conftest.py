import os
import sys
import pytest
import tempfile
from pathlib import Path
import mysql.connector
from mysql.connector import Error

# add the parent directory to the PYTHONPATH
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

from run import app

@pytest.fixture(scope='session', autouse=True)
def setup_test_env():
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_DEBUG'] = 'False'
    os.environ['MYSQL_HOST'] = 'localhost'
    os.environ['MYSQL_USER'] = 'root'
    os.environ['MYSQL_PASSWORD'] = ''
    os.environ['MYSQL_DATABASE'] = 'smartswap_test'
    os.environ['MYSQL_PORT'] = '3306'
    
    try:
        conn = mysql.connector.connect(
            host=os.environ['MYSQL_HOST'],
            user=os.environ['MYSQL_USER'],
            password=os.environ['MYSQL_PASSWORD'],
            ssl_disabled=True,
            auth_plugin='mysql_native_password'
        )
        cursor = conn.cursor()
        
        cursor.execute("DROP DATABASE IF EXISTS smartswap_test")
        cursor.execute("CREATE DATABASE smartswap_test")
        cursor.execute("USE smartswap_test")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                user CHAR(100),
                discord_user_id VARCHAR(125),
                password BLOB,
                PRIMARY KEY (user)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                name VARCHAR(50),
                address VARCHAR(255),
                `keys` BLOB,
                PRIMARY KEY (name)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets_access (
                client_user CHAR(100),
                wallet_name VARCHAR(50),
                PRIMARY KEY (client_user, wallet_name),
                FOREIGN KEY (client_user) REFERENCES clients(user),
                FOREIGN KEY (wallet_name) REFERENCES wallets(name)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funds (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                bot_name VARCHAR(20),
                last_position_id INTEGER,
                funds DECIMAL(18, 8)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cex_market (
                position_id INTEGER PRIMARY KEY AUTO_INCREMENT,
                buy_order_id BIGINT,
                buy_price DECIMAL(18, 8),
                buy_date TIMESTAMP,
                buy_quantity DECIMAL(18, 8),
                buy_fees DECIMAL(18, 8),
                buy_value_usdt DECIMAL(18, 8),
                sell_order_id BIGINT,
                sell_price DECIMAL(18, 8),
                sell_date TIMESTAMP,
                sell_quantity DECIMAL(18, 8),
                sell_fees DECIMAL(18, 8),
                sell_value_usdt DECIMAL(18, 8),
                exchange VARCHAR(20),
                ratio DECIMAL(18, 8),
                position_duration INTEGER,
                pair VARCHAR(20),
                buy_signals TEXT,
                sell_signals TEXT,
                bot_name VARCHAR(20),
                fund_slot INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app (
                position_id INTEGER PRIMARY KEY,
                buy_log BOOLEAN DEFAULT FALSE,
                sell_log BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (position_id) REFERENCES cex_market(position_id)
            )
        """)
        
        conn.commit()
        
    except Error as e:
        print(f"Error setting up test database: {e}")
        raise e
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@pytest.fixture
def app_context():
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    
    # test database configuration
    db_fd, db_path = tempfile.mkstemp()
    app.config['DATABASE'] = db_path
    
    with app.app_context():
        # initialize the test database here if necessary
        pass
    
    yield app
    
    # clean up the test database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers():
    from api.utils.auth import generate_token
    token = generate_token({'user': 'testuser'})
    return {'Authorization': f'Bearer {token}'} 