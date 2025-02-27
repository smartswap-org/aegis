from flask import Blueprint, request, jsonify
from api.database import get_db
from api.utils.crypt_password import encrypt_password, check_password
from api.utils.auth import generate_token, rate_limit, verify_token
from loguru import logger

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
@rate_limit(max_requests=10, window=3600)  # max 10 registrations per hour
def register():
    data = request.get_json()
    
    if not data or not data.get('user') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
        
    # password validation
    if len(data['password']) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400
        
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        # check if user exists
        cursor.execute('SELECT user FROM clients WHERE user = %s', (data['user'],))
        if cursor.fetchone():
            return jsonify({'message': 'Username already exists'}), 400
            
        # create new user
        encrypted_password = encrypt_password(data['password'])
        cursor.execute(
            'INSERT INTO clients (user, discord_user_id, password) VALUES (%s, %s, %s)',
            (data['user'], data.get('discord_user_id'), encrypted_password)
        )
        db.commit()
        
        # generate JWT token
        token = generate_token({
            'user': data['user'],
            'discord_user_id': data.get('discord_user_id')
        })
        
        return jsonify({
            'message': 'User created successfully',
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/login', methods=['POST'])
@rate_limit(max_requests=20, window=60)  # max 20 attempts per minute
def login():
    data = request.get_json()
    
    if not data or not data.get('user') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
        
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('SELECT * FROM clients WHERE user = %s', (data['user'],))
        user = cursor.fetchone()
        
        if not user or not check_password(data['password'], user['password']):
            return jsonify({'message': 'Invalid username or password'}), 401
            
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent_string = request.headers.get('User-Agent', '')
        user_agent = parse(user_agent_string)
        
        accept_language = request.headers.get('Accept-Language', '').split(',')[0]
        referrer = request.headers.get('Referer', '')
        
        cursor.execute('''
            INSERT INTO connection_logs (
                user, ip_address, user_agent, browser, browser_version,
                os, os_version, device_type, language, is_mobile,
                is_tablet, is_bot, referrer
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            )
        ''', (
            user['user'],
            client_ip,
            user_agent_string,
            user_agent.browser.family,
            user_agent.browser.version_string,
            user_agent.os.family,
            user_agent.os.version_string,
            user_agent.device.family,
            accept_language,
            user_agent.is_mobile,
            user_agent.is_tablet,
            user_agent.is_bot,
            referrer
        ))
        
        cursor.execute('''
            DELETE FROM connection_logs 
            WHERE user = %s 
            AND id NOT IN (
                SELECT id FROM (
                    SELECT id 
                    FROM connection_logs 
                    WHERE user = %s 
                    ORDER BY connection_date DESC 
                    LIMIT 10
                ) AS latest
            )
        ''', (user['user'], user['user']))
        
        db.commit()
            
        # generate JWT token
        token = generate_token({
            'user': user['user'],
            'discord_user_id': user['discord_user_id']
        })
        
        return jsonify({
            'user': user['user'],
            'discord_user_id': user['discord_user_id'],
            'token': token
        }), 200
        
    except Exception as e:
        logger.error(f"Error during login: {e}")
        db.rollback()
        return jsonify({'message': f'Error during login: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/logout', methods=['POST'])
def logout():
    # in a real implementation with token blacklist
    return jsonify({'message': 'Logout successful'}), 200

@bp.route('/user', methods=['GET'])
def get_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Missing or invalid token'}), 401
        
    token = auth_header.split(' ')[1]
    try:
        # Verify and decode the token
        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Invalid token'}), 401
            
        db = get_db()
        if not db:
            return jsonify({'message': 'Database connection error'}), 500
            
        cursor = db.cursor(dictionary=True)
        
        try:
            # Get user data from database using the subject from token
            cursor.execute('SELECT user, discord_user_id, power FROM clients WHERE user = %s', (payload['sub'],))
            user_data = cursor.fetchone()
            
            if not user_data:
                return jsonify({'message': 'User not found'}), 404
                
            return jsonify(user_data), 200
            
        except Exception as e:
            logger.error(f"Error fetching user data: {e}")
            return jsonify({'message': 'Error fetching user data'}), 500
        finally:
            cursor.close()
            db.close()
            
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({'message': 'Invalid token'}), 401 