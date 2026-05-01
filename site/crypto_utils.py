import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import config

SECRET_KEY = os.getenv('ENCRYPTION_SECRET', config.ENCRYPTION_SECRET)
SALT_FILE = '.encryption_salt'

def get_encryption_key():
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, 'rb') as f:
            salt = f.read()
    else:
        salt = os.urandom(16)
        with open(SALT_FILE, 'wb') as f:
            f.write(salt)
        try:
            os.chmod(SALT_FILE, 0o600)
        except Exception:
            pass
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return key

_fernet = None

def get_fernet():
    global _fernet
    if _fernet is None:
        key = get_encryption_key()
        _fernet = Fernet(key)
    return _fernet

def encrypt_cookie(cookie: str) -> str:
    try:
        fernet = get_fernet()
        encrypted = fernet.encrypt(cookie.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"Error encrypting cookie: {str(e)}")
        raise

def decrypt_cookie(encrypted_cookie: str) -> str:
    if not encrypted_cookie:
        raise ValueError("Empty encrypted cookie")
    
    try:
        fernet = get_fernet()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_cookie.encode('utf-8'))
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    except Exception:
        raise ValueError("Failed to decrypt cookie")

def is_encrypted(cookie: str) -> bool:
    if not cookie:
        return False
    
    if cookie.startswith('_|WARNING:-DO-NOT-SHARE-THIS'):
        return False
    
    try:
        fernet = get_fernet()
        encrypted_bytes = base64.urlsafe_b64decode(cookie.encode('utf-8'))
        fernet.decrypt(encrypted_bytes)
        return True
    except Exception:
        return False

