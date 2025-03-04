from flask import Blueprint, request, jsonify
from api.database import get_db
from api.utils.crypt_keys import encrypt_keys, decrypt_keys
from api.utils.auth import token_required, is_wallet_owner, rate_limit
from loguru import logger

bp = Blueprint('wallets', __name__, url_prefix='/api/wallets')

@bp.route('/', methods=['POST'])
@token_required
@rate_limit(max_requests=50, window=3600)  # max 50 wallets per hour
def create_wallet(current_user):
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('address') or not data.get('keys'):
        return jsonify({'message': 'Missing required fields'}), 400
        
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        # check if wallet exists
        cursor.execute('SELECT name FROM wallets WHERE name = %s', (data['name'],))
        if cursor.fetchone():
            return jsonify({'message': 'Wallet name already exists'}), 400
            
        # create new wallet with encrypted keys
        encrypted_keys = encrypt_keys(data['keys'])
        cursor.execute(
            'INSERT INTO wallets (name, address, `keys`) VALUES (%s, %s, %s)',
            (data['name'], data['address'], encrypted_keys)
        )
        
        # automatically grant access to creator
        cursor.execute(
            'INSERT INTO wallets_access (client_user, wallet_name) VALUES (%s, %s)',
            (current_user, data['name'])
        )
        
        db.commit()
        
        return jsonify({
            'name': data['name'],
            'address': data['address']
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating wallet: {e}")
        db.rollback()
        return jsonify({'message': f'Error creating wallet: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/<wallet_name>', methods=['GET'])
@token_required
def get_wallet(current_user, wallet_name):
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    if not is_wallet_owner(current_user, wallet_name, db):
        return jsonify({'message': 'Access denied'}), 403
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT w.* 
            FROM wallets w
            JOIN wallets_access wa ON w.name = wa.wallet_name
            WHERE w.name = %s AND wa.client_user = %s
        ''', (wallet_name, current_user))
        
        wallet = cursor.fetchone()
        
        if not wallet:
            return jsonify({'message': 'Wallet not found'}), 404
            
        # decrypt keys before sending
        wallet['keys'] = decrypt_keys(wallet['keys'])
            
        return jsonify(wallet), 200
        
    except Exception as e:
        logger.error(f"Error fetching wallet: {e}")
        return jsonify({'message': f'Error fetching wallet: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/<wallet_name>', methods=['DELETE'])
@token_required
def delete_wallet(current_user, wallet_name):
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    if not is_wallet_owner(current_user, wallet_name, db):
        return jsonify({'message': 'Access denied'}), 403
        
    cursor = db.cursor(dictionary=True)
    
    try:
        # delete access first
        cursor.execute('DELETE FROM wallets_access WHERE wallet_name = %s', (wallet_name,))
        
        # then delete wallet
        cursor.execute('DELETE FROM wallets WHERE name = %s', (wallet_name,))
        db.commit()
        
        return jsonify({'message': 'Wallet deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting wallet: {e}")
        db.rollback()
        return jsonify({'message': f'Error deleting wallet: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/access', methods=['POST'])
@token_required
def grant_wallet_access(current_user):
    data = request.get_json()
    
    if not data or not data.get('client_user') or not data.get('wallet_name'):
        return jsonify({'message': 'Missing required fields'}), 400
        
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    if not is_wallet_owner(current_user, data['wallet_name'], db):
        return jsonify({'message': 'Access denied'}), 403
        
    cursor = db.cursor(dictionary=True)
    
    try:
        # check if client exists
        cursor.execute('SELECT user FROM clients WHERE user = %s', (data['client_user'],))
        if not cursor.fetchone():
            return jsonify({'message': 'Client not found'}), 404
            
        # check if wallet exists
        cursor.execute('SELECT name FROM wallets WHERE name = %s', (data['wallet_name'],))
        if not cursor.fetchone():
            return jsonify({'message': 'Wallet not found'}), 404
            
        # grant access
        cursor.execute(
            'INSERT INTO wallets_access (client_user, wallet_name) VALUES (%s, %s)',
            (data['client_user'], data['wallet_name'])
        )
        db.commit()
        
        return jsonify({'message': 'Wallet access granted successfully'}), 201
        
    except Exception as e:
        logger.error(f"Error granting wallet access: {e}")
        db.rollback()
        return jsonify({'message': f'Error granting wallet access: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/access/<client_user>/<wallet_name>', methods=['DELETE'])
@token_required
def revoke_wallet_access(current_user, client_user, wallet_name):
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    if not is_wallet_owner(current_user, wallet_name, db):
        return jsonify({'message': 'Access denied'}), 403
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute(
            'DELETE FROM wallets_access WHERE client_user = %s AND wallet_name = %s',
            (client_user, wallet_name)
        )
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'message': 'Access not found'}), 404
            
        return jsonify({'message': 'Wallet access revoked successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error revoking wallet access: {e}")
        db.rollback()
        return jsonify({'message': f'Error revoking wallet access: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()

@bp.route('/list', methods=['GET'])
@token_required
def list_client_wallets(current_user):
    db = get_db()
    if not db:
        return jsonify({'message': 'Database connection error'}), 500
        
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT w.name, w.address 
            FROM wallets w
            JOIN wallets_access wa ON w.name = wa.wallet_name
            WHERE wa.client_user = %s
        ''', (current_user,))
        
        wallets = cursor.fetchall()
        return jsonify(wallets), 200
        
    except Exception as e:
        logger.error(f"Error fetching wallets: {e}")
        return jsonify({'message': f'Error fetching wallets: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close() 