import json
import os
import tempfile
import threading

LANDINGS_FILE = 'landings.json'

LANDING_DEFS = {
    'free_gamepass':   ('landings/free_gamepass.html',   '/free-gamepass',   'Free Gamepass'),
    'game_copier':     ('landings/game_copier.html',     '/game-copier',     'Game Copier'),
    'landing_copier':  ('landings/landing_copier.html',  '/copier',          'Studio Copier'),
    'landing_chat':    ('landings/landing_chat.html',    '/chat',            'Chat Unlocker'),
    'landing_region':  ('landings/landing_region.html',  '/region',          'Region Changer'),
    'landing_shaders': ('landings/landing_shaders.html', '/shaders',         'Shaders'),
}

_lock = threading.Lock()


def _load():
    if os.path.exists(LANDINGS_FILE):
        try:
            with open(LANDINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {key: True for key in LANDING_DEFS}


def _save(data):
    dir_name = os.path.dirname(os.path.abspath(LANDINGS_FILE))
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, LANDINGS_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise


def get_all():
    states = _load()
    result = []
    for key, (template, url, name) in LANDING_DEFS.items():
        result.append({
            'key': key,
            'name': name,
            'url': url,
            'template': template,
            'enabled': states.get(key, True),
        })
    return result


def is_enabled(key):
    states = _load()
    return states.get(key, True)


def set_enabled(key, enabled):
    with _lock:
        states = _load()
        states[key] = enabled
        _save(states)
