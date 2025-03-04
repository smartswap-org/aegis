from functools import wraps
from flask import request, jsonify
import jwt
from datetime import datetime, timedelta
from config import Config
import time
from loguru import logger

def generate_token(user_data):
    """Generate a JWT token for the given user data"""
    try:
        # set token expiration to 24 hours from now
        expiration = datetime.utcnow() + timedelta(days=1)
        payload = {
            'exp': expiration,
            'iat': datetime.utcnow(),
            'sub': user_data['user'],
            'discord_user_id': user_data.get('discord_user_id')
        }
        return jwt.encode(
            payload,
            Config.get_flask_config()['secret_key'],
            algorithm='HS256'
        )
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        return None

def verify_token(token):
    """Verify and decode a JWT token"""
    try:
        # decode and validate jwt token
        payload = jwt.decode(
            token, 
            Config.get_flask_config()['secret_key'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None

def token_required(f):
    """Decorator to protect routes with JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # extract token from authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token'}), 401

        if not token:
            return jsonify({'message': 'Missing token'}), 401

        try:
            # validate token and extract user
            data = jwt.decode(
                token,
                Config.get_flask_config()['secret_key'],
                algorithms=['HS256']
            )
            current_user = data['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

def is_wallet_owner(user, wallet_name, db):
    """Check if user has access to wallet."""
    cursor = db.cursor(dictionary=True)
    try:
        # check if user has access to the wallet
        cursor.execute('''
            SELECT 1 
            FROM wallets_access 
            WHERE client_user = %s AND wallet_name = %s
        ''', (user, wallet_name))
        return cursor.fetchone() is not None
    finally:
        cursor.close()

def rate_limit(max_requests, window):
    """Rate limiting decorator"""
    def decorator(f):
        # store request timestamps per ip
        requests = {}
        
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr
            now = time.time()
            
            # clean old requests and check limit
            if ip not in requests:
                requests[ip] = []
            requests[ip] = [t for t in requests[ip] if t > now - window]
            
            if len(requests[ip]) >= max_requests:
                return jsonify({
                    'message': 'Too many requests. Please try again later.'
                }), 429
                
            requests[ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator 