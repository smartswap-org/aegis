from flask import Blueprint, request, jsonify
from api.database import get_db
from api.utils.auth import token_required
from datetime import datetime, timedelta
from loguru import logger

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/overview/<bot_name>', methods=['GET'])
@token_required
def get_overview(current_user, bot_name):
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('SELECT bot_id FROM bots WHERE bot_name = %s', (bot_name,))
        bot = cursor.fetchone()
        if not bot:
            return jsonify({
                'message': 'Bot not found'
            }), 404

        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        cursor.execute('''
            SELECT 
                cm.position_id,
                cm.buy_value_usdc,
                cm.sell_value_usdc,
                cm.buy_fees,
                cm.sell_fees,
                cm.sell_date,
                (cm.sell_value_usdc - cm.buy_value_usdc - cm.buy_fees - cm.sell_fees) as profit
            FROM cex_market cm
            JOIN bots b ON cm.bot_id = b.bot_id
            WHERE cm.sell_date IS NOT NULL
            AND b.bot_name = %s
            ORDER BY cm.sell_date ASC
        ''', (bot_name,))
        positions = cursor.fetchall()
        
        if not positions:
            return jsonify({
                'total_balance': {
                    'amount': 0,
                    'week_change_percentage': 0,
                    'month_change_percentage': 0
                },
                'total_profit': {
                    'all_time': 0,
                    'week': {'amount': 0, 'percentage': 0},
                    'month': {'amount': 0, 'percentage': 0}
                },
                'win_rate': {
                    'all_time': 0,
                    'week': 0,
                    'month': 0
                }
            }), 200
        
        total_balance = 0
        week_balance = 0
        month_balance = 0
        total_profit = 0
        week_profit = 0
        month_profit = 0
        total_trades = 0
        winning_trades = 0
        week_trades = 0
        week_wins = 0
        month_trades = 0
        month_wins = 0
        
        for pos in positions:
            sell_date = pos['sell_date']
            profit = pos['profit']
            
            total_balance += profit
            total_profit += profit
            total_trades += 1
            if profit > 0:
                winning_trades += 1
                
            if sell_date >= week_ago:
                week_balance += profit
                week_profit += profit
                week_trades += 1
                if profit > 0:
                    week_wins += 1
                    
            if sell_date >= month_ago:
                month_balance += profit
                month_profit += profit
                month_trades += 1
                if profit > 0:
                    month_wins += 1
        
        week_change = (week_balance / (total_balance - week_balance) * 100) if total_balance != week_balance else 0
        month_change = (month_balance / (total_balance - month_balance) * 100) if total_balance != month_balance else 0
        
        total_win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        week_win_rate = (week_wins / week_trades * 100) if week_trades > 0 else 0
        month_win_rate = (month_wins / month_trades * 100) if month_trades > 0 else 0
        
        return jsonify({
            'total_balance': {
                'amount': total_balance,
                'week_change_percentage': week_change,
                'month_change_percentage': month_change
            },
            'total_profit': {
                'all_time': total_profit,
                'week': {
                    'amount': week_profit,
                    'percentage': week_change
                },
                'month': {
                    'amount': month_profit,
                    'percentage': month_change
                }
            },
            'win_rate': {
                'all_time': total_win_rate,
                'week': week_win_rate,
                'month': month_win_rate
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching overview data: {e}")
        return jsonify({'message': f'Error fetching overview data: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/performance/<bot_name>', methods=['GET'])
@token_required
def get_performance(current_user, bot_name):
    interval = request.args.get('interval', 'daily')
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('SELECT bot_id FROM bots WHERE bot_name = %s', (bot_name,))
        bot = cursor.fetchone()
        if not bot:
            return jsonify({
                'message': 'Bot not found'
            }), 404

        if interval == 'daily':
            date_format = '%Y-%m-%d'
            group_by = 'DATE(cm.sell_date)'
        elif interval == 'weekly':
            date_format = '%Y-%U'
            group_by = 'YEARWEEK(cm.sell_date)'
        elif interval == 'monthly':
            date_format = '%Y-%m'
            group_by = 'DATE_FORMAT(cm.sell_date, "%Y-%m")'
        else:
            return jsonify({'message': 'Invalid interval'}), 400
            
        cursor.execute(f'''
            SELECT 
                {group_by} as date_group,
                DATE_FORMAT(MIN(cm.sell_date), %s) as period,
                SUM(cm.sell_value_usdc - cm.buy_value_usdc - cm.buy_fees - cm.sell_fees) as profit,
                COUNT(*) as trades
            FROM cex_market cm
            JOIN bots b ON cm.bot_id = b.bot_id
            WHERE cm.sell_date IS NOT NULL
            AND b.bot_name = %s
            GROUP BY date_group
            ORDER BY date_group ASC
        ''', (date_format, bot_name))
        
        performance_data = cursor.fetchall()
        
        running_balance = 0
        result = []
        
        for period in performance_data:
            running_balance += period['profit']
            result.append({
                'date': period['period'],
                'profit': period['profit'],
                'balance': running_balance,
                'trades': period['trades']
            })
            
        return jsonify({
            'interval': interval,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching performance data: {e}")
        return jsonify({'message': f'Error fetching performance data: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/recent-trades/<bot_name>', methods=['GET'])
@token_required
def get_recent_trades(current_user, bot_name):
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit
    
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('SELECT bot_id FROM bots WHERE bot_name = %s', (bot_name,))
        bot = cursor.fetchone()
        if not bot:
            return jsonify({
                'message': 'Bot not found'
            }), 404

        cursor.execute('''
            SELECT COUNT(*) as total
            FROM cex_market cm
            JOIN bots b ON cm.bot_id = b.bot_id
            WHERE b.bot_name = %s
        ''', (bot_name,))
        total = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT 
                cm.position_id,
                cm.pair,
                cm.buy_price as entry_price,
                CASE 
                    WHEN cm.sell_date IS NOT NULL THEN cm.sell_value_usdc - cm.buy_value_usdc - COALESCE(cm.buy_fees, 0) - COALESCE(cm.sell_fees, 0)
                    ELSE NULL
                END as profit_loss,
                CASE 
                    WHEN cm.sell_date IS NOT NULL THEN ((cm.sell_value_usdc - cm.buy_value_usdc - COALESCE(cm.buy_fees, 0) - COALESCE(cm.sell_fees, 0)) / cm.buy_value_usdc * 100)
                    ELSE NULL
                END as profit_loss_percentage,
                CASE 
                    WHEN cm.sell_date IS NOT NULL THEN TIMESTAMPDIFF(DAY, cm.buy_date, cm.sell_date)
                    ELSE TIMESTAMPDIFF(DAY, cm.buy_date, NOW())
                END as duration_days,
                cm.buy_date,
                cm.sell_date,
                cm.exchange,
                cm.buy_value_usdc,
                cm.sell_value_usdc,
                cm.buy_fees,
                cm.sell_fees,
                CASE 
                    WHEN cm.sell_date IS NULL THEN 'OPEN'
                    ELSE 'CLOSED'
                END as status
            FROM cex_market cm
            JOIN bots b ON cm.bot_id = b.bot_id
            WHERE b.bot_name = %s
            ORDER BY COALESCE(cm.sell_date, cm.buy_date) DESC
            LIMIT %s OFFSET %s
        ''', (bot_name, limit, offset))
        
        trades = cursor.fetchall()
        
        return jsonify({
            'trades': trades,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching recent trades: {e}")
        return jsonify({'message': f'Error fetching recent trades: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/trades/<int:position_id>', methods=['GET'])
@token_required
def get_trade_details(current_user, position_id):
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT 
                cm.position_id,
                cm.pair,
                cm.exchange,
                cm.buy_order_id,
                cm.buy_price,
                cm.buy_quantity,
                cm.buy_fees,
                cm.buy_value_usdc,
                cm.buy_date,
                cm.buy_signals,
                cm.sell_order_id,
                cm.sell_price,
                cm.sell_quantity,
                cm.sell_fees,
                cm.sell_value_usdc,
                cm.sell_date,
                cm.sell_signals,
                cm.ratio,
                cm.position_duration,
                cm.fund_slot,
                b.bot_name,
                b.bot_id
            FROM cex_market cm
            JOIN bots b ON cm.bot_id = b.bot_id
            WHERE cm.position_id = %s
        ''', (position_id,))
        
        trade = cursor.fetchone()
        
        if not trade:
            return jsonify({'message': 'Trade not found'}), 404
            
        return jsonify(trade), 200
        
    except Exception as e:
        logger.error(f"Error fetching trade details: {e}")
        return jsonify({'message': f'Error fetching trade details: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()