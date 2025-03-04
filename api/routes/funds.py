from flask import Blueprint, request, jsonify
from api.database import get_db
from loguru import logger

bp = Blueprint('funds', __name__, url_prefix='/api/funds')

@bp.route('/', methods=['POST'])
def create_fund():
    data = request.get_json()
    
    if not data or not data.get('bot_name') or 'funds' not in data:
        return jsonify({'message': 'Missing required fields'}), 400
        
    if not isinstance(data['funds'], (int, float)) or data['funds'] <= 0:
        return jsonify({'message': 'Invalid funds amount'}), 400
        
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT position_id 
            FROM cex_market 
            WHERE bot_name = %s 
            ORDER BY position_id DESC 
            LIMIT 1
        ''', (data['bot_name'],))
        result = cursor.fetchone()
        last_position_id = result['position_id'] if result else 0

        cursor.execute('''
            INSERT INTO funds (bot_name, last_position_id, funds)
            VALUES (%s, %s, %s)
        ''', (data['bot_name'], last_position_id, str(data['funds'])))
        db.commit()
        
        return jsonify({
            'bot_name': data['bot_name'],
            'last_position_id': last_position_id,
            'funds': data['funds']
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating fund: {e}")
        db.rollback()
        return jsonify({'message': f'Error creating fund: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/<bot_name>', methods=['GET'])
def get_fund(bot_name):
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT id, bot_name, last_position_id, funds
            FROM funds 
            WHERE bot_name = %s
            ORDER BY id DESC 
            LIMIT 1
        ''', (bot_name,))
        fund = cursor.fetchone()
        
        if not fund:
            return jsonify({'message': 'Fund not found'}), 404
            
        return jsonify(fund), 200
        
    except Exception as e:
        logger.error(f"Error fetching fund: {e}")
        return jsonify({'message': f'Error fetching fund: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/', methods=['GET'])
def get_funds():
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT f1.*
            FROM funds f1
            INNER JOIN (
                SELECT bot_name, MAX(id) as max_id
                FROM funds
                GROUP BY bot_name
            ) f2 ON f1.bot_name = f2.bot_name AND f1.id = f2.max_id
            ORDER BY f1.bot_name
        ''')
        funds = cursor.fetchall()
        
        return jsonify({'funds': funds}), 200
        
    except Exception as e:
        logger.error(f"Error fetching funds: {e}")
        return jsonify({'message': f'Error fetching funds: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close() 