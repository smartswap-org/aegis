from flask import Blueprint, request, jsonify
from api.database import get_db
from api.utils.crypt_password import encrypt_password, check_password
from api.utils.auth import generate_token, rate_limit
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
        return jsonify({'message': f'Error during login: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/logout', methods=['POST'])
def logout():
    # in a real implementation with token blacklist
    return jsonify({'message': 'Logout successful'}), 200 