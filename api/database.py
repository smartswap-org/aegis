import os
from mysql.connector import connect, Error
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# establish database connection using environment variables
def get_db():
    try:
        connection_params = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'aegis'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'ssl_disabled': True,
            'auth_plugin': 'mysql_native_password'
        }
        
        # adjust connection pool settings based on environment
        if os.getenv('FLASK_ENV') == 'testing':
            connection_params.update({
                'pool_size': 1
            })
        else:
            connection_params.update({
                'connection_timeout': 5,
                'pool_size': 5,
                'pool_name': 'aegis_pool',
                'pool_reset_session': True
            })
            
        # establish database connection
        connection = connect(**connection_params)
        
        # verify database connection is valid
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()['DATABASE()']
        cursor.close()
        
        if not db_name:
            logger.error("No database selected")
            return None
            
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return None 