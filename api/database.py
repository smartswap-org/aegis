import os
from mysql.connector import connect, Error
from config import Config
from loguru import logger

def get_db():
    try:
        # get database configuration from config
        mysql_config = Config.get_mysql_config()
        connection_params = {
            'host': mysql_config['host'],
            'user': mysql_config['user'],
            'password': mysql_config['password'],
            'database': mysql_config['database'],
            'port': mysql_config['port'],
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