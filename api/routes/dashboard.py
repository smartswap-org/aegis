from flask import Blueprint, request, jsonify
from api.database import get_db
from api.utils.auth import token_required
from datetime import datetime, timedelta
from loguru import logger

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/overview/<bot_name>', methods=['GET'])
@token_required
def get_overview(current_user, bot_name):
    """Get total balance, profit, and win rate statistics for a specific bot"""
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        cursor.execute('''
            SELECT 
                position_id,
                buy_value_usdt,
                sell_value_usdt,
                buy_fees,
                sell_fees,
                sell_date,
                (sell_value_usdt - buy_value_usdt - buy_fees - sell_fees) as profit
            FROM cex_market 
            WHERE sell_date IS NOT NULL
            AND bot_name = %s
            ORDER BY sell_date ASC
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
    """Get performance data for graphing for a specific bot"""
    interval = request.args.get('interval', 'daily')
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        if interval == 'daily':
            date_format = '%Y-%m-%d'
            group_by = 'DATE(sell_date)'
        elif interval == 'weekly':
            date_format = '%Y-%U'
            group_by = 'YEARWEEK(sell_date)'
        elif interval == 'monthly':
            date_format = '%Y-%m'
            group_by = 'DATE_FORMAT(sell_date, "%Y-%m")'
        else:
            return jsonify({'message': 'Invalid interval'}), 400
            
        cursor.execute(f'''
            SELECT 
                {group_by} as date_group,
                DATE_FORMAT(MIN(sell_date), %s) as period,
                SUM(sell_value_usdt - buy_value_usdt - buy_fees - sell_fees) as profit,
                COUNT(*) as trades
            FROM cex_market 
            WHERE sell_date IS NOT NULL
            AND bot_name = %s
            GROUP BY date_group
            ORDER BY date_group ASC
        ''', (date_format, bot_name))
        
        performance_data = cursor.fetchall()
        
        # Calculate running balance
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
    """Get list of recent trades for a specific bot"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit
    
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get total count for the specific bot
        cursor.execute('''
            SELECT COUNT(*) as total
            FROM cex_market
            WHERE sell_date IS NOT NULL
            AND bot_name = %s
        ''', (bot_name,))
        total = cursor.fetchone()['total']
        
        # Get paginated trades for the specific bot
        cursor.execute('''
            SELECT 
                position_id,
                pair,
                buy_price as entry_price,
                sell_value_usdt - buy_value_usdt - buy_fees - sell_fees as profit_loss,
                ((sell_value_usdt - buy_value_usdt - buy_fees - sell_fees) / buy_value_usdt * 100) as profit_loss_percentage,
                TIMESTAMPDIFF(DAY, buy_date, sell_date) as duration_days,
                buy_date,
                sell_date,
                exchange,
                buy_value_usdt,
                sell_value_usdt,
                buy_fees,
                sell_fees
            FROM cex_market
            WHERE sell_date IS NOT NULL
            AND bot_name = %s
            ORDER BY sell_date DESC
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
    """Get detailed information about a specific trade"""
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT 
                position_id,
                pair,
                exchange,
                buy_order_id,
                buy_price,
                buy_quantity,
                buy_fees,
                buy_value_usdt,
                buy_date,
                buy_signals,
                sell_order_id,
                sell_price,
                sell_quantity,
                sell_fees,
                sell_value_usdt,
                sell_date,
                sell_signals,
                ratio,
                position_duration,
                bot_name,
                fund_slot
            FROM cex_market
            WHERE position_id = %s
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