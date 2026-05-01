import os
import secrets
import json
import bcrypt


def _load_dotenv(path='.env'):
    if not os.path.exists(path):
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


_load_dotenv()

APP_NAME = 'RbxStudio'

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
CHAT_IDS = [chat_id.strip() for chat_id in os.getenv('CHAT_IDS', '').split(',') if chat_id.strip()]

API_URL = os.getenv('API_URL', 'http://127.0.0.1:8081/api/v1/check')

_SECRET_KEY_FILE = '.secret_key'
_SESSION_NONCE_FILE = '.session_nonce'


def _load_or_generate_secret_key():
    env_key = os.getenv('SECRET_KEY')
    if env_key:
        return env_key
    if os.path.exists(_SECRET_KEY_FILE):
        try:
            with open(_SECRET_KEY_FILE, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if len(key) >= 32:
                    return key
        except Exception:
            pass
    key = secrets.token_hex(32)
    try:
        with open(_SECRET_KEY_FILE, 'w', encoding='utf-8') as f:
            f.write(key)
        os.chmod(_SECRET_KEY_FILE, 0o600)
    except Exception:
        pass
    return key


SECRET_KEY = _load_or_generate_secret_key()
ENCRYPTION_SECRET = os.getenv('ENCRYPTION_SECRET') or SECRET_KEY


def load_session_nonce():
    if os.path.exists(_SESSION_NONCE_FILE):
        try:
            with open(_SESSION_NONCE_FILE, 'r', encoding='utf-8') as f:
                v = f.read().strip()
                if v:
                    return v
        except Exception:
            pass
    nonce = secrets.token_hex(16)
    try:
        with open(_SESSION_NONCE_FILE, 'w', encoding='utf-8') as f:
            f.write(nonce)
        os.chmod(_SESSION_NONCE_FILE, 0o600)
    except Exception:
        pass
    return nonce


def rotate_session_nonce():
    nonce = secrets.token_hex(16)
    try:
        with open(_SESSION_NONCE_FILE, 'w', encoding='utf-8') as f:
            f.write(nonce)
        os.chmod(_SESSION_NONCE_FILE, 0o600)
    except Exception:
        pass
    return nonce

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_FILE = 'admin_password.json'

ADMIN_URL_PATH = '/ljsdkjfsldkajfksdjflkjsdf'

GAME_CODES = {
    'rickdev.rbxl': 109983668079237,
    'plants.rbxl': 127742093697776,
    'baum.rbxl': 126884695634066,
    'mm2.rbxl': 142823291,
    '99nights.rbxl': 79546208627805,
    'adopt.rbxlx': 920587237,
    'bloxfruits.rbxlx': 2753915549,
}


def save_admin_password_hash(password_hash):
    try:
        with open(ADMIN_PASSWORD_FILE, 'w', encoding='utf-8') as f:
            json.dump({'password_hash': password_hash}, f, indent=4)
        try:
            os.chmod(ADMIN_PASSWORD_FILE, 0o600)
        except Exception:
            pass
        return True
    except Exception:
        return False


def load_admin_password_hash():
    env_hash = os.getenv('ADMIN_PASSWORD_HASH')
    if env_hash:
        return env_hash

    env_password = os.getenv('ADMIN_PASSWORD')
    if env_password:
        generated_hash = bcrypt.hashpw(env_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        save_admin_password_hash(generated_hash)
        return generated_hash

    if os.path.exists(ADMIN_PASSWORD_FILE):
        try:
            with open(ADMIN_PASSWORD_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stored = data.get('password_hash', '')
                if stored:
                    return stored
        except Exception:
            pass

    raise RuntimeError('Set ADMIN_PASSWORD or ADMIN_PASSWORD_HASH before first run')


ADMIN_PASSWORD_HASH = load_admin_password_hash()


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_admin_password(password):
    current_hash = load_admin_password_hash()
    try:
        return bcrypt.checkpw(password.encode('utf-8'), current_hash.encode('utf-8'))
    except Exception:
        return False


def update_admin_password(new_password):
    new_hash = hash_password(new_password)
    if save_admin_password_hash(new_hash):
        global ADMIN_PASSWORD_HASH
        ADMIN_PASSWORD_HASH = new_hash
        return True
    return False
