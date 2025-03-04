from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key
import os

# define paths for encryption keys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUBLIC_KEY_PATH = os.path.join(BASE_DIR, "databases", "databases", "encrypt", "keys", "clients_password", "public_key.pem")
PRIVATE_KEY_PATH = os.path.join(BASE_DIR, "databases", "databases", "encrypt", "keys", "clients_password", "private_key.pem")

# load encryption keys
with open(PUBLIC_KEY_PATH, "rb") as public_key_file:
    public_key = load_pem_public_key(public_key_file.read())

with open(PRIVATE_KEY_PATH, "rb") as private_key_file:
    private_key = load_pem_private_key(private_key_file.read(), password=None)

def encrypt_password(password):
    # encrypt password using RSA with OAEP padding
    encrypted_password = public_key.encrypt(
        password.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_password

def decrypt_password(encrypted_password):
    # decrypt password using private RSA key
    decrypted_password = private_key.decrypt(
        encrypted_password,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_password.decode('utf-8')

def check_password(plain_password, encrypted_password):
    # safely compare plain password with encrypted one
    try:
        decrypted = decrypt_password(encrypted_password)
        return decrypted == plain_password
    except Exception:
        return False

def get_client_password(cursor, username):
    # retrieve encrypted password from database
    cursor.execute("""
        SELECT password
        FROM clients
        WHERE user = %s
    """, (username,))
    result = cursor.fetchone()
    if result:
        return decrypt_password(result['password'])
    return None 