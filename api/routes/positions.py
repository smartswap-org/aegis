from flask import Blueprint, request, jsonify
from api.database import get_db
from api.utils.auth import token_required
from loguru import logger

bp = Blueprint('positions', __name__, url_prefix='/api/positions')

@bp.route('/', methods=['POST'])
@token_required
def create_position(current_user):
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No input data provided'}), 400
        
    required_fields = ['buy_order_id', 'buy_price', 'buy_quantity', 'buy_fees',
                      'buy_value_usdc', 'exchange', 'pair', 'bot_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
            
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('SELECT bot_id FROM bots WHERE bot_name = %s', (data['bot_name'],))
        bot = cursor.fetchone()
        if not bot:
            return jsonify({'message': f'Bot {data["bot_name"]} not found'}), 404
            
        cursor.execute('''
            INSERT INTO cex_market (
                buy_order_id, buy_price, buy_quantity, buy_fees, 
                buy_value_usdc, exchange, pair, bot_id, buy_date,
                buy_signals, fund_slot
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
        ''', (
            data['buy_order_id'], data['buy_price'], data['buy_quantity'],
            data['buy_fees'], data['buy_value_usdc'], data['exchange'],
            data['pair'], bot['bot_id'], data.get('buy_signals'),
            data.get('fund_slot', 0)
        ))
        position_id = cursor.lastrowid
        
        cursor.execute(
            'INSERT INTO app (position_id) VALUES (%s)',
            (position_id,)
        )
        db.commit()
        
        return jsonify({
            'message': 'Position created successfully',
            'position_id': position_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating position: {e}")
        db.rollback()
        return jsonify({'message': f'Error creating position: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/', methods=['GET'])
@token_required
def get_positions(current_user):
    bot_name = request.args.get('bot_name')
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        query = '''
            SELECT cm.*, a.buy_log, a.sell_log
            FROM cex_market cm
            LEFT JOIN app a ON cm.position_id = a.position_id
        '''
        params = []
        
        if bot_name:
            query += '''
                JOIN bots b ON cm.bot_id = b.bot_id
                WHERE b.bot_name = %s
            '''
            params.append(bot_name)
            
        query += ' ORDER BY cm.buy_date DESC'
        
        cursor.execute(query, params)
        positions = cursor.fetchall()
        
        return jsonify({'positions': positions}), 200
        
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return jsonify({'message': f'Error fetching positions: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/<int:position_id>/sell', methods=['PUT'])
@token_required
def update_position(current_user, position_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No input data provided'}), 400
        
    required_fields = ['sell_order_id', 'sell_price', 'sell_quantity',
                      'sell_fees', 'sell_value_usdc']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
            
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            UPDATE cex_market SET
                sell_order_id = %s,
                sell_price = %s,
                sell_quantity = %s,
                sell_fees = %s,
                sell_value_usdc = %s,
                sell_date = NOW(),
                sell_signals = %s,
                ratio = (sell_value_usdc - buy_value_usdc) / buy_value_usdc,
                position_duration = TIMESTAMPDIFF(SECOND, buy_date, NOW())
            WHERE position_id = %s
        ''', (
            data['sell_order_id'], data['sell_price'], data['sell_quantity'],
            data['sell_fees'], data['sell_value_usdc'], data.get('sell_signals'),
            position_id
        ))
        
        if cursor.rowcount == 0:
            return jsonify({'message': 'Position not found'}), 404
            
        if 'sell_log' in data:
            cursor.execute(
                'UPDATE app SET sell_log = %s WHERE position_id = %s',
                (data['sell_log'], position_id)
            )
            
        db.commit()
        return jsonify({'message': 'Position updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating position: {e}")
        db.rollback()
        return jsonify({'message': f'Error updating position: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close() 