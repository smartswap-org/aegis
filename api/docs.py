from flask_restx import Api, Resource, fields, Namespace
from flask import Blueprint, request, jsonify, url_for
from api.database import get_db
from loguru import logger
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

# Secret key for JWT
JWT_SECRET = os.getenv('FLASK_SECRET_KEY', 'smartswap')

# api documentation blueprint
bp = Blueprint('docs', __name__)
api = Api(bp,
    title='AEGIS API Documentation',
    version='1.0',
    description='''Complete documentation of the AEGIS API
    
Power Levels:
- 5 (SYS.ADMIN): System administrator with full access
- 4 (DEVELOPER): Development team member
- 3 (REVIEWER): Code reviewer
- 2 (VIP): VIP client with extended access
- 1 (CLIENT): Standard client
- 0 (VISITOR): Basic visitor access
''',
    prefix='/api',
    doc='/',
    default='AEGIS',
    default_label='AEGIS API Endpoints',
    validate=True,
    ordered=True
)

# custom swagger ui configuration
@api.documentation
def custom_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AEGIS API Documentation</title>
        <meta charset="UTF-8">
        <link rel="stylesheet" type="text/css" href="/swaggerui/swagger-ui.css">
        <link rel="icon" type="image/png" href="/assets/logo.png" sizes="32x32">
        <style>
            .swagger-ui .topbar { 
                background-color: white; 
                padding: 10px;
            }
            .swagger-ui .topbar .download-url-wrapper { display: none; }
            .swagger-ui .topbar-wrapper img {
                content: url("/assets/logo.png");
                height: 200px;
                width: auto;
                margin-right: 10px;
            }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="/swaggerui/swagger-ui-bundle.js"></script>
        <script src="/swaggerui/swagger-ui-standalone-preset.js"></script>
        <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "/api/swagger.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            })
            window.ui = ui
        }
        </script>
    </body>
    </html>
    """

# api namespaces definition
auth_ns = api.namespace('auth', description='Authentication operations')
wallets_ns = api.namespace('wallets', description='Wallet management')
positions_ns = api.namespace('positions', description='Trading operations')
funds_ns = api.namespace('funds', description='Fund management')
dashboard_ns = api.namespace('dashboard', description='Dashboard operations')
bots_ns = api.namespace('bots', description='Bot management')

# models for request/response validation
register_model = api.model('Register', {
    'user': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password (min. 8 characters)'),
    'discord_user_id': fields.String(required=False, description='Discord user ID'),
    'power': fields.Integer(required=False, description='Power level (0-VISITOR, 1-CLIENT, 2-VIP, 3-REVIEWER, 4-DEVELOPER, 5-SYS.ADMIN)', default=0)
})

login_model = api.model('Login', {
    'user': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

auth_response = api.model('AuthResponse', {
    'user': fields.String(description='Username'),
    'discord_user_id': fields.String(description='Discord ID'),
    'token': fields.String(description='JWT Token'),
    'power': fields.Integer(description='Power level (0-VISITOR, 1-CLIENT, 2-VIP, 3-REVIEWER, 4-DEVELOPER, 5-SYS.ADMIN)')
})

power_update_model = api.model('PowerUpdate', {
    'power': fields.Integer(required=True, description='New power level (0-5)')
})

wallet_model = api.model('Wallet', {
    'name': fields.String(required=True, description='Wallet name'),
    'address': fields.String(required=True, description='Wallet address'),
    'keys': fields.Raw(required=True, description='Wallet keys (private/public)')
})

wallet_access_model = api.model('WalletAccess', {
    'client_user': fields.String(required=True, description='User to grant access to'),
    'wallet_name': fields.String(required=True, description='Wallet name')
})

position_model = api.model('Position', {
    'buy_order_id': fields.String(required=True, description='Buy order ID'),
    'buy_price': fields.Float(required=True, description='Buy price'),
    'buy_quantity': fields.Float(required=True, description='Buy quantity'),
    'buy_fees': fields.Float(required=True, description='Buy fees'),
    'buy_value_usdc': fields.Float(required=True, description='Value in USDC'),
    'exchange': fields.String(required=True, description='Exchange used'),
    'pair': fields.String(required=True, description='Trading pair'),
    'bot_name': fields.String(required=True, description='Bot name'),
    'buy_signals': fields.String(required=False, description='Buy signals'),
    'fund_slot': fields.Integer(required=False, description='Fund slot')
})

position_response = api.model('PositionResponse', {
    'position_id': fields.Integer(description='Position ID'),
    'buy_order_id': fields.String(description='Buy order ID'),
    'buy_price': fields.Float(description='Buy price'),
    'buy_quantity': fields.Float(description='Buy quantity'),
    'buy_fees': fields.Float(description='Buy fees'),
    'buy_value_usdc': fields.Float(description='Value in USDC'),
    'exchange': fields.String(description='Exchange used'),
    'pair': fields.String(description='Trading pair'),
    'bot_name': fields.String(description='Bot name'),
    'buy_signals': fields.String(description='Buy signals'),
    'fund_slot': fields.Integer(description='Fund slot'),
    'buy_date': fields.DateTime(description='Buy date'),
    'buy_log': fields.Boolean(description='Buy log'),
    'sell_log': fields.Boolean(description='Sell log')
})

position_update_model = api.model('PositionUpdate', {
    'sell_order_id': fields.String(required=True, description='Sell order ID'),
    'sell_price': fields.Float(required=True, description='Sell price'),
    'sell_quantity': fields.Float(required=True, description='Sell quantity'),
    'sell_fees': fields.Float(required=True, description='Sell fees'),
    'sell_value_usdc': fields.Float(required=True, description='Value in USDC'),
    'sell_signals': fields.String(required=False, description='Sell signals'),
    'sell_log': fields.Boolean(required=False, description='Sell log')
})

fund_model = api.model('Fund', {
    'bot_name': fields.String(required=True, description='Bot name'),
    'funds': fields.Float(required=True, description='Fund amount')
})

fund_response = api.model('FundResponse', {
    'id': fields.Integer(description='Fund ID'),
    'bot_name': fields.String(description='Bot name'),
    'last_position_id': fields.Integer(description='Last position ID'),
    'funds': fields.Float(description='Fund amount')
})

# Add dashboard namespace
dashboard_ns = api.namespace('dashboard', description='Dashboard operations')

# Models for dashboard responses
balance_model = api.model('Balance', {
    'amount': fields.Float(description='Balance amount in USDC'),
    'week_change_percentage': fields.Float(description='Weekly change percentage'),
    'month_change_percentage': fields.Float(description='Monthly change percentage')
})

profit_period_model = api.model('ProfitPeriod', {
    'amount': fields.Float(description='Profit amount in USDC'),
    'percentage': fields.Float(description='Change percentage for the period')
})

profit_model = api.model('Profit', {
    'all_time': fields.Float(description='All-time profit in USDC'),
    'week': fields.Nested(profit_period_model),
    'month': fields.Nested(profit_period_model)
})

win_rate_model = api.model('WinRate', {
    'all_time': fields.Float(description='All-time win rate percentage'),
    'week': fields.Float(description='Weekly win rate percentage'),
    'month': fields.Float(description='Monthly win rate percentage')
})

overview_response = api.model('Overview', {
    'total_balance': fields.Nested(balance_model),
    'total_profit': fields.Nested(profit_model),
    'win_rate': fields.Nested(win_rate_model)
})

performance_data_model = api.model('PerformanceData', {
    'date': fields.String(description='Period date'),
    'profit': fields.Float(description='Period profit'),
    'balance': fields.Float(description='Running balance'),
    'trades': fields.Integer(description='Number of trades in period')
})

performance_response = api.model('Performance', {
    'interval': fields.String(description='Data interval (daily/weekly/monthly)'),
    'data': fields.List(fields.Nested(performance_data_model))
})

trade_model = api.model('Trade', {
    'position_id': fields.Integer(description='Position ID'),
    'pair': fields.String(description='Trading pair'),
    'entry_price': fields.Float(description='Entry price'),
    'profit_loss': fields.Float(description='Profit/Loss in USDC'),
    'profit_loss_percentage': fields.Float(description='Profit/Loss percentage'),
    'duration_days': fields.Integer(description='Trade duration in days'),
    'buy_date': fields.DateTime(description='Entry date'),
    'sell_date': fields.DateTime(description='Exit date'),
    'exchange': fields.String(description='Exchange name')
})

pagination_model = api.model('Pagination', {
    'total': fields.Integer(description='Total number of records'),
    'page': fields.Integer(description='Current page number'),
    'limit': fields.Integer(description='Records per page'),
    'pages': fields.Integer(description='Total number of pages')
})

trades_response = api.model('Trades', {
    'trades': fields.List(fields.Nested(trade_model)),
    'pagination': fields.Nested(pagination_model)
})

trade_detail_model = api.model('TradeDetail', {
    'position_id': fields.Integer(description='Position ID'),
    'pair': fields.String(description='Trading pair'),
    'exchange': fields.String(description='Exchange name'),
    'buy_order_id': fields.Integer(description='Buy order ID'),
    'buy_price': fields.Float(description='Buy price'),
    'buy_quantity': fields.Float(description='Buy quantity'),
    'buy_fees': fields.Float(description='Buy fees'),
    'buy_value_usdc': fields.Float(description='Buy value in USDC'),
    'buy_date': fields.DateTime(description='Buy date'),
    'buy_signals': fields.String(description='Buy signals'),
    'sell_order_id': fields.Integer(description='Sell order ID'),
    'sell_price': fields.Float(description='Sell price'),
    'sell_quantity': fields.Float(description='Sell quantity'),
    'sell_fees': fields.Float(description='Sell fees'),
    'sell_value_usdc': fields.Float(description='Sell value in USDC'),
    'sell_date': fields.DateTime(description='Sell date'),
    'sell_signals': fields.String(description='Sell signals'),
    'ratio': fields.Float(description='Profit/Loss ratio'),
    'position_duration': fields.Integer(description='Position duration in seconds'),
    'bot_name': fields.String(description='Bot name'),
    'fund_slot': fields.Integer(description='Fund slot')
})

bot_model = api.model('Bot', {
    'name': fields.String(required=True, description='Bot name'),
    'strategy': fields.String(required=True, description='Trading strategy'),
    'exchange_name': fields.String(required=True, description='Exchange name'),
    'pairs': fields.String(required=True, description='Trading pairs'),
    'reinvest_gains': fields.Boolean(required=False, description='Whether to reinvest gains', default=False),
    'position_percent_invest': fields.Float(required=False, description='Percentage to invest per position', default=100.0),
    'invest_capital': fields.Float(required=False, description='Initial capital to invest', default=0.0),
    'adjust_with_profits_if_loss': fields.Boolean(required=False, description='Adjust capital with profits if loss occurs', default=False),
    'timeframe': fields.String(required=False, description='Trading timeframe', default='1h'),
    'simulation': fields.Boolean(required=False, description='Whether this is a simulation bot', default=False),
    'status': fields.Boolean(required=False, description='Bot status (active/inactive)', default=False)
})

bot_response = api.model('BotResponse', {
    'id': fields.Integer(description='Bot ID'),
    'name': fields.String(description='Bot name'),
    'strategy': fields.String(description='Trading strategy'),
    'exchange_name': fields.String(description='Exchange name'),
    'pairs': fields.String(description='Trading pairs'),
    'reinvest_gains': fields.Boolean(description='Whether to reinvest gains'),
    'position_percent_invest': fields.Float(description='Percentage to invest per position'),
    'invest_capital': fields.Float(description='Initial capital to invest'),
    'adjust_with_profits_if_loss': fields.Boolean(description='Adjust capital with profits if loss occurs'),
    'timeframe': fields.String(description='Trading timeframe'),
    'simulation': fields.Boolean(description='Whether this is a simulation bot'),
    'status': fields.Boolean(description='Bot status'),
    'current_funds': fields.Float(description='Current funds'),
    'total_positions': fields.Integer(description='Total number of positions')
})

# authentication endpoints
@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(register_model)
    @auth_ns.response(201, 'User created successfully', auth_response)
    @auth_ns.response(400, 'Invalid data')
    @auth_ns.response(500, 'Server error')
    def post(self):
        """create a new user account"""
        pass

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login successful', auth_response)
    @auth_ns.response(401, 'Invalid credentials')
    @auth_ns.response(500, 'Server error')
    def post(self):
        """login and get JWT token"""
        pass

@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.response(200, 'Logout successful')
    def post(self):
        """logout current user"""
        pass

@auth_ns.route('/user/<string:username>/power')
class UserPower(Resource):
    @auth_ns.doc(security='Bearer')
    @auth_ns.expect(power_update_model)
    @auth_ns.response(200, 'Power level updated successfully')
    @auth_ns.response(401, 'Unauthorized')
    @auth_ns.response(403, 'Forbidden - Insufficient privileges')
    @auth_ns.response(404, 'User not found')
    def put(self, username):
        """update user power level (requires SYS.ADMIN privileges)"""
        pass

@auth_ns.route('/user')
class UserInfo(Resource):
    @auth_ns.doc(security='Bearer')
    @auth_ns.response(200, 'Success', auth_response)
    @auth_ns.response(401, 'Unauthorized')
    def get(self):
        """get current user information"""
        try:
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                return {'error': 'No token provided'}, 401

            try:
                # Décoder le token JWT
                payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                username = payload.get('user')
                if not username:
                    return {'error': 'Invalid token'}, 401
            except jwt.InvalidTokenError:
                return {'error': 'Invalid token'}, 401

            db = get_db()
            if not db:
                return {'error': 'Database connection error'}, 500

            cursor = db.cursor(dictionary=True)
            try:
                cursor.execute("""
                    SELECT user, discord_user_id, power
                    FROM clients
                    WHERE user = %s
                """, (username,))
                
                user_data = cursor.fetchone()
                if not user_data:
                    return {'error': 'User not found'}, 404

                return {
                    'user': user_data['user'],
                    'discord_user_id': user_data['discord_user_id'],
                    'power': user_data['power']
                }, 200

            finally:
                cursor.close()
                db.close()

        except Exception as e:
            logger.error(f"Error in user info: {e}")
            return {'error': str(e)}, 500

@auth_ns.route('/check')
class AuthCheck(Resource):
    @auth_ns.doc(security='Bearer')
    @auth_ns.response(200, 'Token is valid', auth_response)
    @auth_ns.response(401, 'Token is invalid or expired')
    def get(self):
        """verify if the current token is valid"""
        try:
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                return {'authenticated': False}, 401

            try:
                # Décoder le token JWT
                payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                username = payload.get('user')
                if not username:
                    return {'authenticated': False}, 401
            except jwt.InvalidTokenError:
                return {'authenticated': False}, 401

            db = get_db()
            if not db:
                return {'error': 'Database connection error'}, 500

            cursor = db.cursor(dictionary=True)
            try:
                cursor.execute("""
                    SELECT user, discord_user_id, power
                    FROM clients
                    WHERE user = %s
                """, (username,))
                
                user_data = cursor.fetchone()
                if not user_data:
                    return {'authenticated': False}, 401

                return {
                    'authenticated': True,
                    'user': user_data['user'],
                    'discord_user_id': user_data['discord_user_id'],
                    'power': user_data['power']
                }, 200

            finally:
                cursor.close()
                db.close()

        except Exception as e:
            logger.error(f"Error in auth check: {e}")
            return {'authenticated': False}, 401

# wallet management endpoints
@wallets_ns.route('/')
class WalletList(Resource):
    @wallets_ns.expect(wallet_model)
    @wallets_ns.response(201, 'Wallet created successfully')
    @wallets_ns.response(400, 'Invalid data')
    @wallets_ns.response(500, 'Server error')
    def post(self):
        """create a new wallet"""
        pass

@wallets_ns.route('/<wallet_name>')
class Wallet(Resource):
    @wallets_ns.response(200, 'Success')
    @wallets_ns.response(403, 'Access denied')
    @wallets_ns.response(404, 'Wallet not found')
    def get(self, wallet_name):
        """get wallet details"""
        pass

    @wallets_ns.response(200, 'Wallet deleted successfully')
    @wallets_ns.response(403, 'Access denied')
    @wallets_ns.response(404, 'Wallet not found')
    def delete(self, wallet_name):
        """delete a wallet"""
        pass

@wallets_ns.route('/access')
class WalletAccess(Resource):
    @wallets_ns.expect(wallet_access_model)
    @wallets_ns.response(201, 'Access granted successfully')
    @wallets_ns.response(403, 'Access denied')
    @wallets_ns.response(404, 'User or wallet not found')
    def post(self):
        """grant wallet access to user"""
        data = request.get_json()
        
        if not data or not data.get('client_user') or not data.get('wallet_name'):
            return {'message': 'Missing required fields'}, 400
            
        db = get_db()
        if not db:
            return {'message': 'Database connection error'}, 500
            
        cursor = db.cursor(dictionary=True)
        
        try:
            # Check if user exists
            cursor.execute('SELECT 1 FROM clients WHERE user = %s', (data['client_user'],))
            if not cursor.fetchone():
                return {'message': 'User not found'}, 404
                
            # Check if wallet exists
            cursor.execute('SELECT 1 FROM wallets WHERE name = %s', (data['wallet_name'],))
            if not cursor.fetchone():
                return {'message': 'Wallet not found'}, 404
                
            # Grant access
            cursor.execute('''
                INSERT INTO wallets_access (client_user, wallet_name)
                VALUES (%s, %s)
            ''', (data['client_user'], data['wallet_name']))
            
            db.commit()
            return {'message': 'Access granted successfully'}, 201
            
        except Exception as e:
            db.rollback()
            return {'message': f'Error granting access: {str(e)}'}, 500
        finally:
            cursor.close()
            db.close()

@wallets_ns.route('/access/<client_user>/<wallet_name>')
class WalletAccessRevoke(Resource):
    @wallets_ns.response(200, 'Access revoked successfully')
    @wallets_ns.response(403, 'Access denied')
    @wallets_ns.response(404, 'Access not found')
    def delete(self, client_user, wallet_name):
        """revoke wallet access from user"""
        pass

@wallets_ns.route('/list')
class WalletsList(Resource):
    @wallets_ns.response(200, 'Success')
    @wallets_ns.response(500, 'Server error')
    def get(self):
        """Get a list of all wallets that the authenticated client has access to"""
        pass

# positions routes
@positions_ns.route('/')
class PositionList(Resource):
    @positions_ns.doc(security='Bearer')
    @positions_ns.expect(position_model)
    @positions_ns.response(201, 'Position created successfully')
    @positions_ns.response(400, 'Invalid data')
    @positions_ns.response(401, 'Unauthorized')
    @positions_ns.response(500, 'Server error')
    def post(self):
        """Create a new position"""
        data = request.get_json()
        if not data:
            return {'message': 'No input data provided'}, 400
            
        db = get_db()
        if not db:
            return {'message': 'Database connection error'}, 500
            
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute('''
                INSERT INTO cex_market (
                    buy_order_id, buy_price, buy_quantity, buy_fees, 
                    buy_value_usdc, exchange, pair, bot_name, buy_date,
                    buy_signals, fund_slot
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
            ''', (
                data['buy_order_id'], data['buy_price'], data['buy_quantity'],
                data['buy_fees'], data['buy_value_usdc'], data['exchange'],
                data['pair'], data['bot_name'], data.get('buy_signals'),
                data.get('fund_slot', 0)
            ))
            position_id = cursor.lastrowid
            
            cursor.execute(
                'INSERT INTO app (position_id) VALUES (%s)',
                (position_id,)
            )
            db.commit()
            
            return {
                'message': 'Position created successfully',
                'position_id': position_id
            }, 201
        except Exception as e:
            logger.error(f"Error creating position: {e}")
            db.rollback()
            return {'message': f'Error creating position: {str(e)}'}, 500
        finally:
            cursor.close()
            db.close()

    @positions_ns.doc(security='Bearer')
    @positions_ns.response(200, 'Success', [position_response])
    @positions_ns.response(401, 'Unauthorized')
    @positions_ns.response(500, 'Server error')
    def get(self):
        """Get all positions"""
        db = get_db()
        if not db:
            return {'message': 'Database connection error'}, 500
            
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute('''
                SELECT cm.*, a.buy_log, a.sell_log
                FROM cex_market cm
                LEFT JOIN app a ON cm.position_id = a.position_id
                ORDER BY cm.buy_date DESC
            ''')
            positions = cursor.fetchall()
            return {'positions': positions}, 200
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return {'message': f'Error fetching positions: {str(e)}'}, 500
        finally:
            cursor.close()
            db.close()

@positions_ns.route('/<int:position_id>/sell')
class PositionSell(Resource):
    @positions_ns.doc(security='Bearer')
    @positions_ns.expect(position_update_model)
    @positions_ns.response(200, 'Position updated successfully')
    @positions_ns.response(401, 'Unauthorized')
    @positions_ns.response(404, 'Position not found')
    @positions_ns.response(500, 'Server error')
    def put(self, position_id):
        """Update position with sell information"""
        data = request.get_json()
        if not data:
            return {'message': 'No input data provided'}, 400
            
        db = get_db()
        if not db:
            return {'message': 'Database connection error'}, 500
            
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
                return {'message': 'Position not found'}, 404
                
            if 'sell_log' in data:
                cursor.execute(
                    'UPDATE app SET sell_log = %s WHERE position_id = %s',
                    (data['sell_log'], position_id)
                )
                
            db.commit()
            return {'message': 'Position updated successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            db.rollback()
            return {'message': f'Error updating position: {str(e)}'}, 500
        finally:
            cursor.close()
            db.close()

# funds routes
@funds_ns.route('/')
class FundList(Resource):
    @funds_ns.expect(fund_model)
    @funds_ns.response(201, 'Fund created successfully')
    @funds_ns.response(400, 'Invalid data')
    @funds_ns.response(500, 'Server error')
    def post(self):
        """Create a new fund"""
        data = request.get_json()
        if not data:
            return {'message': 'No input data provided'}, 400
            
        db = get_db()
        if not db:
            return {'message': 'Database connection error'}, 500
            
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute('''
                INSERT INTO funds (bot_name, funds)
                VALUES (%s, %s)
            ''', (data['bot_name'], data['funds']))
            db.commit()
            return {'message': 'Fund created successfully'}, 201
        except Exception as e:
            logger.error(f"Error creating fund: {e}")
            db.rollback()
            return {'message': f'Error creating fund: {str(e)}'}, 500
        finally:
            cursor.close()
            db.close()

    @funds_ns.response(200, 'Success', [fund_response])
    def get(self):
        """Get all funds"""
        db = get_db()
        if not db:
            return {'message': 'Database connection error'}, 500
            
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
            return {'funds': funds}, 200
        except Exception as e:
            logger.error(f"Error fetching funds: {e}")
            return {'message': f'Error fetching funds: {str(e)}'}, 500
        finally:
            cursor.close()
            db.close()

@funds_ns.route('/<bot_name>')
class Fund(Resource):
    @funds_ns.response(200, 'Success', fund_response)
    @funds_ns.response(404, 'Fund not found')
    def get(self, bot_name):
        """Get fund for specific bot"""
        db = get_db()
        if not db:
            return {'message': 'Database connection error'}, 500
            
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
                return {'message': 'Fund not found'}, 404
                
            return fund, 200
        except Exception as e:
            logger.error(f"Error fetching fund: {e}")
            return {'message': f'Error fetching fund: {str(e)}'}, 500
        finally:
            cursor.close()
            db.close()

# Dashboard routes
@dashboard_ns.route('/overview/<bot_name>')
@dashboard_ns.param('bot_name', 'Name of the bot to get overview for')
class DashboardOverview(Resource):
    @dashboard_ns.doc(security='Bearer')
    @dashboard_ns.response(200, 'Success', overview_response)
    @dashboard_ns.response(401, 'Unauthorized')
    @dashboard_ns.response(500, 'Server error')
    def get(self, bot_name):
        """Get dashboard overview including total balance, profit, and win rates for a specific bot"""
        pass

@dashboard_ns.route('/performance/<bot_name>')
@dashboard_ns.param('bot_name', 'Name of the bot to get performance for')
class DashboardPerformance(Resource):
    @dashboard_ns.doc(security='Bearer')
    @dashboard_ns.param('interval', 'Data interval (daily/weekly/monthly)', _in='query', default='daily')
    @dashboard_ns.response(200, 'Success', performance_response)
    @dashboard_ns.response(400, 'Invalid interval')
    @dashboard_ns.response(401, 'Unauthorized')
    @dashboard_ns.response(500, 'Server error')
    def get(self, bot_name):
        """Get performance data for graphing for a specific bot"""
        pass

@dashboard_ns.route('/recent-trades/<bot_name>')
@dashboard_ns.param('bot_name', 'Name of the bot to get trades for')
class RecentTrades(Resource):
    @dashboard_ns.doc(security='Bearer')
    @dashboard_ns.param('page', 'Page number', _in='query', type=int, default=1)
    @dashboard_ns.param('limit', 'Records per page', _in='query', type=int, default=10)
    @dashboard_ns.response(200, 'Success', trades_response)
    @dashboard_ns.response(401, 'Unauthorized')
    @dashboard_ns.response(500, 'Server error')
    def get(self, bot_name):
        """Get list of recent trades for a specific bot"""
        pass

@dashboard_ns.route('/trades/<int:position_id>')
class TradeDetails(Resource):
    @dashboard_ns.doc(security='Bearer')
    @dashboard_ns.response(200, 'Success', trade_detail_model)
    @dashboard_ns.response(401, 'Unauthorized')
    @dashboard_ns.response(404, 'Trade not found')
    @dashboard_ns.response(500, 'Server error')
    def get(self, position_id):
        """Get detailed information about a specific trade"""
        pass

@bots_ns.route('/')
class BotList(Resource):
    @bots_ns.doc(security='Bearer')
    @bots_ns.expect(bot_model)
    @bots_ns.response(201, 'Bot created successfully', bot_response)
    @bots_ns.response(400, 'Invalid data')
    @bots_ns.response(401, 'Unauthorized')
    @bots_ns.response(409, 'Bot name already exists')
    @bots_ns.response(500, 'Server error')
    def post(self):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return {'error': 'No token provided'}, 401

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            username = payload.get('sub')
            if not username:
                return {'error': 'Invalid token'}, 401
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}, 401

        data = request.get_json()
        
        required_fields = ['name', 'strategy', 'exchange_name', 'pairs']
        for field in required_fields:
            if not data or not data.get(field):
                return {'message': f'Missing required field: {field}'}, 400
            
        db = get_db()
        if not db:
            return {'message': 'Database connection error'}, 500
            
        cursor = db.cursor(dictionary=True)
        
        try:
            cursor.execute('SELECT bot_id FROM bots WHERE bot_name = %s', (data['name'],))
            if cursor.fetchone():
                return {'message': 'Bot name already exists'}, 409

            cursor.execute('''
                INSERT INTO bots (
                    bot_name, strategy, exchange_name, pairs,
                    reinvest_gains, position_percent_invest, invest_capital,
                    adjust_with_profits_if_loss, timeframe, simulation, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                data['name'],
                data['strategy'],
                data['exchange_name'],
                data['pairs'],
                data.get('reinvest_gains', False),
                data.get('position_percent_invest', 100.0),
                data.get('invest_capital', 0.0),
                data.get('adjust_with_profits_if_loss', False),
                data.get('timeframe', '1h'),
                data.get('simulation', False),
                data.get('status', False)
            ))
            db.commit()
            
            bot_id = cursor.lastrowid
            
            return {
                'id': bot_id,
                'name': data['name'],
                'strategy': data['strategy'],
                'exchange_name': data['exchange_name'],
                'pairs': data['pairs'],
                'reinvest_gains': data.get('reinvest_gains', False),
                'position_percent_invest': data.get('position_percent_invest', 100.0),
                'invest_capital': data.get('invest_capital', 0.0),
                'adjust_with_profits_if_loss': data.get('adjust_with_profits_if_loss', False),
                'timeframe': data.get('timeframe', '1h'),
                'simulation': data.get('simulation', False),
                'status': data.get('status', False)
            }, 201
            
        except Exception as e:
            logger.error(f"Error creating bot: {e}")
            db.rollback()
            return {'message': f'Error creating bot: {str(e)}'}, 500
        finally:
            cursor.close()
            db.close()

    @bots_ns.doc(security='Bearer')
    @bots_ns.response(200, 'Success', [bot_response])
    @bots_ns.response(401, 'Unauthorized')
    @bots_ns.response(500, 'Server error')
    def get(self):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return {'error': 'No token provided'}, 401

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            username = payload.get('sub')
            if not username:
                return {'error': 'Invalid token'}, 401
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}, 401

        db = get_db()
        if not db:
            return {'message': 'Database connection error'}, 500
            
        cursor = db.cursor(dictionary=True)
        
        try:
            cursor.execute('''
                SELECT 
                    b.bot_id as id,
                    b.bot_name as name,
                    b.strategy,
                    b.exchange_name,
                    b.pairs,
                    b.reinvest_gains,
                    b.position_percent_invest,
                    b.invest_capital,
                    b.adjust_with_profits_if_loss,
                    b.timeframe,
                    b.simulation,
                    b.status,
                    f.funds as current_funds,
                    COUNT(DISTINCT p.position_id) as total_positions
                FROM bots b
                LEFT JOIN (
                    SELECT bot_id, funds
                    FROM funds f1
                    WHERE id = (
                        SELECT MAX(id)
                        FROM funds f2
                        WHERE f1.bot_id = f2.bot_id
                    )
                ) f ON b.bot_id = f.bot_id
                LEFT JOIN cex_market p ON b.bot_id = p.bot_id
                GROUP BY b.bot_id, f.funds
                ORDER BY b.bot_id DESC
            ''')
            bots = cursor.fetchall()
            
            return {'bots': bots}, 200
            
        except Exception as e:
            logger.error(f"Error fetching bots: {e}")
            return {'message': f'Error fetching bots: {str(e)}'}, 500
        finally:
            cursor.close()
            db.close()

@bots_ns.route('/<bot_name>')
class Bot(Resource):
    @bots_ns.doc(security='Bearer')
    @bots_ns.response(200, 'Success', bot_response)
    @bots_ns.response(401, 'Unauthorized')
    @bots_ns.response(404, 'Bot not found')
    @bots_ns.response(500, 'Server error')
    def get(self, bot_name):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return {'error': 'No token provided'}, 401

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            username = payload.get('sub')
            if not username:
                return {'error': 'Invalid token'}, 401
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}, 401

        db = get_db()
        if not db:
            return {'message': 'Database connection error'}, 500
            
        cursor = db.cursor(dictionary=True)
        
        try:
            cursor.execute('''
                SELECT 
                    bot_id as id,
                    bot_name as name,
                    strategy,
                    exchange_name,
                    pairs,
                    reinvest_gains,
                    position_percent_invest,
                    invest_capital,
                    adjust_with_profits_if_loss,
                    timeframe,
                    simulation,
                    status
                FROM bots
                WHERE bot_name = %s
            ''', (bot_name,))
            
            bot = cursor.fetchone()
            if not bot:
                return {'message': 'Bot not found'}, 404

            cursor.execute('''
                SELECT funds
                FROM funds
                WHERE bot_id = %s
                ORDER BY id DESC
                LIMIT 1
            ''', (bot['id'],))
            
            funds_row = cursor.fetchone()
            bot['current_funds'] = funds_row['funds'] if funds_row else None

            cursor.execute('''
                SELECT COUNT(DISTINCT position_id) as total
                FROM cex_market
                WHERE bot_id = %s
            ''', (bot['id'],))
            
            positions = cursor.fetchone()
            bot['total_positions'] = positions['total'] if positions else 0
                
            return bot, 200
            
        except Exception as e:
            logger.error(f"Error fetching bot: {e}")
            return {'message': f'Error fetching bot: {str(e)}'}, 500
        finally:
            cursor.close()
            db.close() 