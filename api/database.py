import os
import mysql.connector
from mysql.connector import Error
from loguru import logger

# establish database connection using environment variables
def get_db():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),   
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB')
        )
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()['DATABASE()']
        cursor.close()
        
        if not db_name:
            logger.error("No database selected")
            return None
            
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL database: {e}")
        return None 