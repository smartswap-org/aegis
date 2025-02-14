from flask_restx import Api, Resource, fields
from flask import Blueprint, request, jsonify, url_for
from api.database import get_db
from loguru import logger

# api documentation blueprint
bp = Blueprint('docs', __name__)
api = Api(bp,
    title='AEGIS API Documentation',
    version='1.0',
    description='Complete documentation of the AEGIS API',
    prefix='/api',
    doc='/',
    default='AEGIS',
    default_label='AEGIS API Endpoints'
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

# models for request/response validation
register_model = api.model('Register', {
    'user': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password (min. 8 characters)'),
    'discord_user_id': fields.String(required=False, description='Discord user ID')
})

login_model = api.model('Login', {
    'user': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

auth_response = api.model('AuthResponse', {
    'user': fields.String(description='Username'),
    'discord_user_id': fields.String(description='Discord ID'),
    'token': fields.String(description='JWT Token')
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
    'buy_value_usdt': fields.Float(required=True, description='Value in USDT'),
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
    'buy_value_usdt': fields.Float(description='Value in USDT'),
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
    'sell_value_usdt': fields.Float(required=True, description='Value in USDT'),
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

# positions routes
@positions_ns.route('/')
class PositionList(Resource):
    @positions_ns.expect(position_model)
    @positions_ns.response(201, 'Position created successfully')
    @positions_ns.response(400, 'Invalid data')
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
                    buy_value_usdt, exchange, pair, bot_name, buy_date,
                    buy_signals, fund_slot
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
            ''', (
                data['buy_order_id'], data['buy_price'], data['buy_quantity'],
                data['buy_fees'], data['buy_value_usdt'], data['exchange'],
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

    @positions_ns.response(200, 'Success', [position_response])
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
    @positions_ns.expect(position_update_model)
    @positions_ns.response(200, 'Position updated successfully')
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
                    sell_value_usdt = %s,
                    sell_date = NOW(),
                    sell_signals = %s,
                    ratio = (sell_value_usdt - buy_value_usdt) / buy_value_usdt,
                    position_duration = TIMESTAMPDIFF(SECOND, buy_date, NOW())
                WHERE position_id = %s
            ''', (
                data['sell_order_id'], data['sell_price'], data['sell_quantity'],
                data['sell_fees'], data['sell_value_usdt'], data.get('sell_signals'),
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