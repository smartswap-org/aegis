from functools import wraps
from flask import request, jsonify
import jwt
from datetime import datetime, timedelta
from config import Config

def generate_token(user_data):
    """Generate a JWT token for a user."""
    try:
        payload = {
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'sub': user_data['user'],
            'discord_user_id': user_data.get('discord_user_id')
        }
        return jwt.encode(
            payload,
            Config.get_flask_config()['secret_key'],
            algorithm='HS256'
        )
    except Exception:
        return None

def token_required(f):
    """Decorator to protect routes with JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # check if token is in header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token'}), 401

        if not token:
            return jsonify({'message': 'Missing token'}), 401

        try:
            # decode token
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
        cursor.execute('''
            SELECT 1 
            FROM wallets_access 
            WHERE client_user = %s AND wallet_name = %s
        ''', (user, wallet_name))
        return cursor.fetchone() is not None
    finally:
        cursor.close()

def rate_limit(max_requests=100, window=60):
    """Decorator to limit request rate."""
    def decorator(f):
        # store requests by IP
        requests = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # get client IP
            ip = request.remote_addr
            now = datetime.now()
            
            # clean old requests
            if ip in requests:
                requests[ip] = [req for req in requests[ip] if (now - req).total_seconds() < window]
            
            # check limit
            if ip in requests and len(requests[ip]) >= max_requests:
                return jsonify({'message': 'Too many requests'}), 429
            
            # add request
            if ip not in requests:
                requests[ip] = []
            requests[ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator 