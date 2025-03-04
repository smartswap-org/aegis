from flask import Blueprint, request, jsonify
from api.database import get_db
from api.utils.auth import token_required
from loguru import logger

bp = Blueprint('bots', __name__, url_prefix='/api/bots')

@bp.route('/', methods=['POST'])
@token_required
def create_bot(current_user):
    data = request.get_json()
    
    if not data or not data.get('bot_name') or not data.get('wallet_name'):
        return jsonify({'message': 'Missing required fields'}), 400
        
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        # Check if bot name already exists
        cursor.execute('SELECT bot_id FROM bots WHERE bot_name = %s', (data['bot_name'],))
        if cursor.fetchone():
            return jsonify({'message': 'Bot name already exists'}), 400
            
        # Check if wallet exists
        cursor.execute('SELECT name FROM wallets WHERE name = %s', (data['wallet_name'],))
        wallet = cursor.fetchone()
        if not wallet:
            return jsonify({'message': 'Wallet not found'}), 404

        # Create bot
        cursor.execute('''
            INSERT INTO bots (
                client_user, wallet_name, bot_name, exchange_name, pairs,
                strategy, reinvest_gains, position_percent_invest, invest_capital,
                adjust_with_profits_if_loss, timeframe, simulation, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            current_user,
            data['wallet_name'],
            data['bot_name'],
            data.get('exchange_name', 'Binance'),
            data.get('pairs', '[]'),
            data.get('strategy', 'default'),
            data.get('reinvest_gains', True),
            data.get('position_percent_invest', 50.00),
            data.get('invest_capital', 1000.00),
            data.get('adjust_with_profits_if_loss', True),
            data.get('timeframe', '1h'),
            data.get('simulation', True),
            False
        ))
        bot_id = cursor.lastrowid
        db.commit()
        
        return jsonify({
            'message': 'Bot created successfully',
            'bot_id': bot_id,
            'bot_name': data['bot_name']
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        db.rollback()
        return jsonify({'message': f'Error creating bot: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/', methods=['GET'])
@token_required
def get_bots(current_user):
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT b.bot_id, b.bot_name, b.description, b.wallet_name
            FROM bots b
            JOIN wallets w ON b.wallet_id = w.wallet_id
            ORDER BY b.bot_name
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
@token_required
def get_bot(current_user, bot_name):
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT b.bot_id, b.bot_name, b.description, w.name as wallet_name
            FROM bots b
            JOIN wallets w ON b.wallet_id = w.wallet_id
            WHERE b.bot_name = %s
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