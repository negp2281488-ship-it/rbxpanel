import hashlib
import hmac
import time
from functools import wraps
from flask import request, redirect, url_for, make_response
import config

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300
_login_attempts = {}
_LOGIN_MAX_KEYS = 5000


def _is_rate_limited(ip):
    now = time.time()

    if len(_login_attempts) > _LOGIN_MAX_KEYS:
        cutoff = now - LOCKOUT_SECONDS
        stale = [k for k, v in _login_attempts.items() if not v or v[-1] < cutoff]
        for k in stale:
            del _login_attempts[k]

    if ip not in _login_attempts:
        _login_attempts[ip] = []
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < LOCKOUT_SECONDS]
    return len(_login_attempts[ip]) >= MAX_LOGIN_ATTEMPTS


def _record_attempt(ip):
    if ip not in _login_attempts:
        _login_attempts[ip] = []
    _login_attempts[ip].append(time.time())


def _get_key_material():
    pw_hash = config.load_admin_password_hash()
    nonce = config.load_session_nonce()
    return f"{config.SECRET_KEY}:{pw_hash}:{nonce}".encode()


def generate_auth_token(username):
    timestamp = str(int(time.time()))
    message = f"{username}:{timestamp}"
    token = hmac.new(
        _get_key_material(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{username}:{timestamp}:{token}"


def verify_auth_token(token):
    try:
        parts = token.split(':')
        if len(parts) != 3:
            return False

        username, timestamp, received_token = parts

        if int(time.time()) - int(timestamp) > 86400:
            return False

        message = f"{username}:{timestamp}"
        expected_token = hmac.new(
            _get_key_material(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(received_token, expected_token) and username == config.ADMIN_USERNAME
    except Exception:
        return False


def verify_credentials(username, password):
    ip = request.remote_addr or '0.0.0.0'
    if _is_rate_limited(ip):
        return False
    _record_attempt(ip)
    return (username == config.ADMIN_USERNAME and
            config.verify_admin_password(password))


def change_password(old_password, new_password):
    if not config.verify_admin_password(old_password):
        return False, "Wrong current password"

    if len(new_password) < 8:
        return False, "Password must be at least 8 characters"

    if config.update_admin_password(new_password):
        return True, "Password updated"
    return False, "Failed to save password"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_token = request.cookies.get('admin_token')

        if not auth_token or not verify_auth_token(auth_token):
            response = make_response(redirect(url_for('admin_login')))
            response.set_cookie('admin_token', '', expires=0)
            return response

        return f(*args, **kwargs)
    return decorated_function
