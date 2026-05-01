                                                                                                                                  #!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from api_client import RobloxAPI
from proxy_manager import proxy_manager
import traceback
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


def format_account_age(created_str):
    try:
        created_dt = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
        age_delta = datetime.now(created_dt.tzinfo) - created_dt
        
        days = age_delta.days
        if days < 1:
            hours = age_delta.seconds // 3600
            return f"{hours} час(ов)"
        elif days < 30:
            return f"{days} дней"
        elif days < 365:
            months = days // 30
            return f"{months} месяц(ев)"
        else:
            years = days // 365
            remaining_days = days % 365
            if remaining_days > 30:
                months = remaining_days // 30
                return f"{years} год(а), {months} месяц(ев)"
            else:
                return f"{years} год(а)"
    except Exception:
        return "N/A"


def check_cookie_detailed(cookie: str) -> dict:
    result = {
        'success': False,
        'valid': False,
        'error': None,
        'data': None,
        'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        if not cookie or len(cookie) < 100:
            result['error'] = 'Cookie слишком короткий или пустой'
            return result
        
        if not cookie.startswith('_|WARNING'):
            result['error'] = 'Cookie должен начинаться с _|WARNING:-DO-NOT-SHARE'
            return result
        
        api = RobloxAPI(cookie)
        
        try:
            if not api.get_authenticated_user():
                result['error'] = 'Cookie невалиден или истек'
                return result
        except requests.exceptions.Timeout:
            result['error'] = 'Превышено время ожидания при проверке cookie (таймаут)'
            return result
        
        result['valid'] = True
        
        data = {
            'user_id': api.user_id,
            'username': api.username,
        }
        
        try:
            details = api.get_user_details()
            if details:
                data['display_name'] = details.get('displayName')
                data['description'] = details.get('description')
                data['created'] = details.get('created')
                data['is_banned'] = details.get('isBanned', False)
                data['has_verified_badge'] = details.get('hasVerifiedBadge', False)
                
                if details.get('created'):
                    data['account_age'] = format_account_age(details.get('created'))
        except Exception as e:
            data['details_error'] = str(e)
        
        try:
            robux = api.get_robux_balance()
            data['robux'] = robux if robux is not None else 0
        except Exception as e:
            data['robux'] = None
            data['robux_error'] = str(e)
        
        try:
            pending = api.get_pending_robux()
            data['pending_robux'] = pending if pending is not None else 0
        except Exception as e:
            data['pending_robux'] = None
        
        try:
            rap = api.get_rap()
            data['rap'] = rap if rap is not None else 0
        except Exception as e:
            data['rap'] = None
        
        try:
            premium = api.get_premium_status()
            data['premium'] = premium if premium else False
        except Exception as e:
            data['premium'] = False
        
        try:
            location = api.get_account_location()
            data['location'] = location if location else 'Unknown'
        except Exception as e:
            data['location'] = 'Unknown'
        
        try:
            groups = api.get_groups_count()
            data['groups_count'] = groups if groups is not None else 0
        except Exception as e:
            data['groups_count'] = None
        
        try:
            friends = api.get_friends_count()
            data['friends_count'] = friends if friends is not None else 0
        except Exception as e:
            data['friends_count'] = None
        
        try:
            followers = api.get_followers_count()
            data['followers_count'] = followers if followers is not None else 0
        except Exception as e:
            data['followers_count'] = None
        
        try:
            presence = api.get_user_presence()
            if presence:
                status_map = {
                    0: 'Offline',
                    1: 'Online',
                    2: 'In Game',
                    3: 'In Studio'
                }
                data['presence'] = {
                    'status': status_map.get(presence.get('userPresenceType', 0), 'Unknown'),
                    'last_location': presence.get('lastLocation'),
                    'last_online': presence.get('lastOnline')
                }
        except Exception as e:
            data['presence'] = None
        
        try:
            twofa = api.get_two_factor_status()
            if twofa:
                data['two_factor'] = {
                    'enabled': twofa.get('enabled', False),
                    'methods': twofa.get('methods', []),
                    'pin_enabled': twofa.get('pin_enabled', False)
                }
        except Exception as e:
            data['two_factor'] = None
        
        try:
            email_info = api.get_email_info()
            if email_info:
                data['email'] = {
                    'address': email_info.get('email'),
                    'verified': email_info.get('verified', False),
                    'domain': email_info.get('domain')
                }
        except Exception as e:
            data['email'] = None
        
        try:
            badges = api.get_badges_info()
            if badges:
                data['badges'] = {
                    'total_count': badges.get('total_count', 0),
                    'recent_badges': [
                        {
                            'name': badge.get('name'),
                            'description': badge.get('description')
                        } 
                        for badge in badges.get('recent_badges', [])[:5]
                    ]
                }
        except Exception as e:
            data['badges'] = None
        
        try:
            expensive = api.check_expensive_items()
            if expensive:
                data['expensive_items'] = expensive
        except Exception as e:
            data['expensive_items'] = None
        
        try:
            total_inv = api.get_total_inventory_count()
            data['inventory_total'] = total_inv if total_inv is not None else 0
        except Exception as e:
            data['inventory_total'] = None
        
        try:
            inventory = api.get_inventory_summary()
            if inventory:
                data['inventory_details'] = inventory
        except Exception as e:
            data['inventory_details'] = None
        
        try:
            transactions = api.get_transaction_summary()
            if transactions:
                data['transactions'] = transactions
        except Exception as e:
            data['transactions'] = None
        
        try:
            credit = api.get_credit_balance()
            data['credit_balance'] = credit if credit is not None else 0.0
        except Exception as e:
            data['credit_balance'] = None
        
        try:
            payment_methods = api.get_payment_methods_count()
            data['payment_methods_count'] = payment_methods if payment_methods is not None else 0
        except Exception as e:
            data['payment_methods_count'] = None
        
        try:
            game_purchases = api.get_game_purchases()
            if game_purchases:
                data['game_purchases'] = game_purchases
        except Exception as e:
            data['game_purchases'] = None
        
        try:
            robux_sources = api.get_robux_sources()
            if robux_sources:
                data['robux_sources'] = robux_sources
        except Exception as e:
            data['robux_sources'] = None
        
        result['success'] = True
        result['data'] = data
        
    except requests.exceptions.Timeout:
        result['error'] = 'Превышено время ожидания ответа от Roblox API (таймаут). Попробуйте еще раз.'
        result['timeout'] = True
    except requests.exceptions.ConnectionError:
        result['error'] = 'Ошибка подключения к Roblox API. Проверьте интернет-соединение.'
    except Exception as e:
        # Не выводим traceback и детали ошибки, чтобы не раскрывать куки
        error_msg = str(e) if 'cookie' not in str(e).lower() else 'Ошибка при проверке cookie'
        result['error'] = error_msg
    
    return result


@app.route('/api/v1/check', methods=['POST'])
def check_cookie():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Не передан JSON в теле запроса'
            }), 400
        
        cookie = data.get('cookie')
        detailed = data.get('detailed', True)
        use_proxy = data.get('use_proxy', True)  # По умолчанию используем прокси
        
        if not cookie:
            return jsonify({
                'success': False,
                'error': 'Параметр "cookie" обязателен'
            }), 400
        
        logger.info(f"Проверка cookie с использованием прокси: {use_proxy}")
        result = check_cookie_detailed(cookie)
        
        if not detailed and result['success'] and result['data']:
            basic_data = {
                'user_id': result['data'].get('user_id'),
                'username': result['data'].get('username'),
                'display_name': result['data'].get('display_name'),
                'robux': result['data'].get('robux'),
                'premium': result['data'].get('premium'),
                'created': result['data'].get('created'),
                'is_banned': result['data'].get('is_banned', False)
            }
            result['data'] = basic_data
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        # Не выводим traceback в production, чтобы не раскрывать чувствительные данные
        error_msg = str(e) if 'cookie' not in str(e).lower() else 'Внутренняя ошибка сервера'
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


def check_single_cookie_threaded(cookie: str, index: int, detailed: bool) -> dict:
    """
    Проверяет один cookie в отдельном потоке
    
    Args:
        cookie: Cookie для проверки
        index: Индекс в массиве
        detailed: Возвращать ли детальную информацию
    
    Returns:
        Результат проверки с индексом
    """
    try:
        result = check_cookie_detailed(cookie)
        
        if not detailed and result['success'] and result['data']:
            basic_data = {
                'user_id': result['data'].get('user_id'),
                'username': result['data'].get('username'),
                'robux': result['data'].get('robux'),
                'premium': result['data'].get('premium'),
            }
            result['data'] = basic_data
        
        return {
            'index': index + 1,
            'cookie': cookie[:50] + "..." if len(cookie) > 50 else cookie,
            'result': result
        }
    except Exception as e:
        return {
            'index': index + 1,
            'cookie': cookie[:50] + "..." if len(cookie) > 50 else cookie,
            'result': {
                'success': False,
                'valid': False,
                'error': f'Ошибка в потоке: {str(e)}',
                'data': None
            }
        }


@app.route('/api/v1/check-batch', methods=['POST'])
def check_cookies_batch():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Не передан JSON в теле запроса'
            }), 400
        
        cookies = data.get('cookies', [])
        detailed = data.get('detailed', False)
        max_workers = data.get('max_workers', 10)  # Максимум потоков параллельно
        
        if not cookies or not isinstance(cookies, list):
            return jsonify({
                'success': False,
                'error': 'Параметр "cookies" должен быть массивом'
            }), 400
        
        if len(cookies) > 100:
            return jsonify({
                'success': False,
                'error': 'Максимум 100 cookies за раз'
            }), 400
        
        # Ограничиваем количество потоков
        max_workers = min(max_workers, 20)  # Не более 20 потоков
        max_workers = min(max_workers, len(cookies))  # Не больше чем куков
        
        logger.info(f"Запуск batch проверки {len(cookies)} куков с {max_workers} потоками")
        
        results = []
        valid_count = 0
        invalid_count = 0
        
        # Используем ThreadPoolExecutor для параллельной обработки
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Отправляем все задачи на выполнение
            future_to_index = {
                executor.submit(check_single_cookie_threaded, cookie, i, detailed): i 
                for i, cookie in enumerate(cookies)
            }
            
            # Собираем результаты по мере выполнения
            for future in as_completed(future_to_index):
                try:
                    result_data = future.result()
                    results.append(result_data)
                    
                    if result_data['result'].get('valid'):
                        valid_count += 1
                    else:
                        invalid_count += 1
                        
                except Exception as e:
                    index = future_to_index[future]
                    logger.error(f"Ошибка при обработке cookie #{index + 1}: {e}")
                    results.append({
                        'index': index + 1,
                        'cookie': cookies[index][:50] + "..." if len(cookies[index]) > 50 else cookies[index],
                        'result': {
                            'success': False,
                            'valid': False,
                            'error': f'Критическая ошибка: {str(e)}',
                            'data': None
                        }
                    })
                    invalid_count += 1
        
        # Сортируем результаты по индексу для правильного порядка
        results.sort(key=lambda x: x['index'])
        
        logger.info(f"Batch проверка завершена: {valid_count} валидных, {invalid_count} невалидных")
        
        return jsonify({
            'success': True,
            'summary': {
                'total': len(cookies),
                'valid': valid_count,
                'invalid': invalid_count,
                'valid_percentage': round((valid_count / len(cookies)) * 100, 2) if len(cookies) > 0 else 0
            },
            'results': results
        }), 200
        
    except Exception as e:
        # Не выводим traceback в production, чтобы не раскрывать чувствительные данные
        error_msg = str(e) if 'cookie' not in str(e).lower() else 'Внутренняя ошибка сервера'
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@app.route('/api/v1/proxy/status', methods=['GET'])
def proxy_status():
    """Возвращает статус прокси менеджера"""
    try:
        return jsonify({
            'success': True,
            'total_proxies': len(proxy_manager.proxies),
            'working_proxies_cached': proxy_manager.get_working_proxies_count(),
            'proxy_file': proxy_manager.proxy_file
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/proxy/reload', methods=['POST'])
def proxy_reload():
    """Перезагружает список прокси и очищает кэш"""
    try:
        proxy_manager.load_proxies()
        proxy_manager.clear_working_cache()
        return jsonify({
            'success': True,
            'message': 'Прокси перезагружены',
            'total_proxies': len(proxy_manager.proxies)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    logger.info(f"Загружено {len(proxy_manager.proxies)} прокси")
    app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
