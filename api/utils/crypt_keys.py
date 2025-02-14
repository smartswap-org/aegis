from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUBLIC_KEY_PATH = os.path.join(BASE_DIR, "databases", "databases", "encrypt", "keys", "wallets_keys", "public_key.pem")
PRIVATE_KEY_PATH = os.path.join(BASE_DIR, "databases", "databases", "encrypt", "keys", "wallets_keys", "private_key.pem")

with open(PUBLIC_KEY_PATH, "rb") as public_key_file:
    public_key = load_pem_public_key(public_key_file.read())

with open(PRIVATE_KEY_PATH, "rb") as private_key_file:
    private_key = load_pem_private_key(private_key_file.read(), password=None)

def encrypt_keys(keys):
    """Encrypt the keys using the public RSA key."""
    keys_json = json.dumps(keys)
    encrypted_keys = public_key.encrypt(
        keys_json.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_keys

def decrypt_keys(encrypted_keys):
    """Decrypt the keys using the private RSA key."""
    decrypted_keys = private_key.decrypt(
        encrypted_keys,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    keys_json = decrypted_keys.decode('utf-8')
    return json.loads(keys_json) 