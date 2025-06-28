from flask import Blueprint, jsonify
from api.database import get_db
from loguru import logger
import datetime

bp = Blueprint('health', __name__, url_prefix='/api/health')

@bp.route('/', methods=['GET'])
def health_check():
    try:
        db = get_db()
        if not db:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed',
                'timestamp': datetime.datetime.utcnow().isoformat()
            }), 500
            
        cursor = db.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT 1=1 as test_result")
            result = cursor.fetchone()
            
            if result and result['test_result'] == 1:
                return jsonify({
                    'status': 'healthy',
                    'message': 'Database connection successful',
                    'database': 'connected',
                    'timestamp': datetime.datetime.utcnow().isoformat()
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Database query test failed',
                    'timestamp': datetime.datetime.utcnow().isoformat()
                }), 500
                
        except Exception as e:
            logger.error(f"Database query error in health check: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Database query failed: {str(e)}',
                'timestamp': datetime.datetime.utcnow().isoformat()
            }), 500
        finally:
            cursor.close()
            db.close()
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 500 