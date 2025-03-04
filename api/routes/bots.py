from flask import Blueprint, request, jsonify
from api.database import get_db
from loguru import logger

bp = Blueprint('bots', __name__, url_prefix='/api/bots')

@bp.route('/', methods=['POST'])
def create_bot():
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('strategy'):
        return jsonify({'message': 'Missing required fields'}), 400
        
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('SELECT bot_id FROM bots WHERE bot_name = %s', (data['name'],))
        if cursor.fetchone():
            return jsonify({'message': 'Bot name already exists'}), 409

        cursor.execute('''
            INSERT INTO bots (bot_name, strategy, status)
            VALUES (%s, %s, %s)
        ''', (data['name'], data['strategy'], data.get('status', 'inactive')))
        db.commit()
        
        bot_id = cursor.lastrowid
        
        return jsonify({
            'id': bot_id,
            'name': data['name'],
            'strategy': data['strategy'],
            'status': data.get('status', 'inactive')
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        db.rollback()
        return jsonify({'message': f'Error creating bot: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/', methods=['GET'])
def get_bots():
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT bot_id as id, bot_name as name, strategy, status, created_at
            FROM bots
            ORDER BY created_at DESC
        ''')
        bots = cursor.fetchall()
        
        return jsonify({'bots': bots}), 200
        
    except Exception as e:
        logger.error(f"Error fetching bots: {e}")
        return jsonify({'message': f'Error fetching bots: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/<bot_name>', methods=['GET'])
def get_bot(bot_name):
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT 
                b.bot_id as id,
                b.bot_name as name,
                b.strategy,
                b.status,
                b.created_at,
                f.funds as current_funds,
                COUNT(DISTINCT p.position_id) as total_positions
            FROM bots b
            LEFT JOIN funds f ON b.bot_id = f.bot_id
            LEFT JOIN cex_market p ON b.bot_id = p.bot_id
            WHERE b.bot_name = %s
            GROUP BY b.bot_id, f.funds
            ORDER BY f.id DESC
            LIMIT 1
        ''', (bot_name,))
        bot = cursor.fetchone()
        
        if not bot:
            return jsonify({'message': 'Bot not found'}), 404
            
        return jsonify(bot), 200
        
    except Exception as e:
        logger.error(f"Error fetching bot: {e}")
        return jsonify({'message': f'Error fetching bot: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close() 