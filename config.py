import os
from dotenv import load_dotenv
import json
from loguru import logger

# load the environment variables from the .env file
load_dotenv()

class Config:
    _config = None

    @staticmethod
    def load_config():
        if Config._config is None:
            try:
                with open('config.json', 'r') as f:
                    Config._config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                raise

    @staticmethod
    def get_mysql_config():
        Config.load_config()
        return Config._config['mysql']

    @staticmethod
    def get_flask_config():
        Config.load_config()
        return Config._config['flask']

    # application settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'smartswap')
    
    # database configurations    
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))

    # flask configuration
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true' and os.getenv('FLASK_ENV', 'production') != 'production'

    @staticmethod
    def get_mysql_config():
        return {
            'host': Config.MYSQL_HOST,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'database': Config.MYSQL_DATABASE,
            'port': Config.MYSQL_PORT
        }

    @staticmethod
    def get_flask_config():
        return {
            'secret_key': Config.FLASK_SECRET_KEY,
            'debug': Config.FLASK_DEBUG
        }
