#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API клиент для взаимодействия с Roblox API
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import API_ENDPOINTS, EXPENSIVE_ITEMS, ASSET_TYPES, COUNTRY_NAMES, TRANSACTION_TYPES, REQUEST_TIMEOUT, LONG_REQUEST_TIMEOUT
import logging

logger = logging.getLogger(__name__)


class RobloxAPI:
    """Класс для работы с Roblox API"""
    
    def __init__(self, roblosecurity_cookie: str, use_proxy: bool = True, proxy_dict: Optional[Dict[str, str]] = None):
        """
        Инициализация API клиента
        
        Args:
            roblosecurity_cookie: Cookie .ROBLOSECURITY для аутентификации
            use_proxy: Использовать ли прокси (по умолчанию True)
            proxy_dict: Словарь с настройками прокси (если None, будет выбран случайный)
        """
        self.cookie = roblosecurity_cookie
        self.session = requests.Session()
        self.session.cookies.set('.ROBLOSECURITY', roblosecurity_cookie, domain='.roblox.com')
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        self.created_date: Optional[datetime] = None
        self.use_proxy = use_proxy
        self.proxy_dict = proxy_dict
        
        # Настройка прокси
        if self.use_proxy:
            if self.proxy_dict:
                self.session.proxies.update(self.proxy_dict)
                logger.info("Прокси установлен для сессии")
            else:
                # Импортируем здесь чтобы избежать циклических импортов
                from proxy_manager import proxy_manager
                # Получаем случайный прокси (сначала пробует из кэша, потом новые)
                self.proxy_dict = proxy_manager.get_random_working_proxy(max_attempts=3)
                if self.proxy_dict:
                    self.session.proxies.update(self.proxy_dict)
                    logger.info("Рабочий прокси установлен для сессии")
                else:
                    logger.warning("Не удалось найти рабочий прокси, работа без прокси")
                    self.use_proxy = False
    
    def get_authenticated_user(self) -> bool:
        """Получает информацию об аутентифицированном пользователе"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['users']}/v1/users/authenticated",
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 401:
                return False
            
            response.raise_for_status()
            data = response.json()
            
            self.user_id = data.get('id')
            self.username = data.get('name')
            
            return self.user_id is not None
            
        except requests.exceptions.Timeout:
            return False
        except requests.exceptions.RequestException:
            return False
    
    def get_user_details(self) -> Optional[Dict[str, Any]]:
        """Получает детальную информацию о пользователе"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['users']}/v1/users/{self.user_id}",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            created = data.get('created')
            if created:
                self.created_date = datetime.fromisoformat(created.replace('Z', '+00:00'))
            
            return data
            
        except requests.exceptions.RequestException:
            return None
    
    def get_account_location(self) -> Optional[str]:
        """Получает местоположение аккаунта"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['users']}/v1/users/authenticated/country-code",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            country_code = data.get('countryCode')
            
            if country_code:
                return COUNTRY_NAMES.get(country_code, f'🌍 {country_code}')
            return None
            
        except requests.exceptions.RequestException:
            return None
    
    def get_user_presence(self) -> Optional[Dict[str, Any]]:
        """Получает информацию об активности пользователя"""
        try:
            response = self.session.post(
                f"{API_ENDPOINTS['presence']}/v1/presence/users",
                json={'userIds': [self.user_id]},
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('userPresences'):
                return data['userPresences'][0]
            return None
            
        except requests.exceptions.RequestException:
            return None
    
    def get_premium_status(self) -> Optional[bool]:
        """Проверяет Premium статус"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['premium']}/v1/users/{self.user_id}/validate-membership",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException:
            return None
    
    def get_robux_balance(self) -> Optional[int]:
        """Получает баланс Robux"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['economy']}/v1/users/{self.user_id}/currency",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data.get('robux', 0)
            
        except requests.exceptions.RequestException:
            return None
    
    def get_pending_robux(self) -> Optional[int]:
        """Получает количество Robux в ожидании"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['economy']}/v2/users/{self.user_id}/transaction-totals",
                params={'timeFrame': 'Month', 'transactionType': 'summary'},
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data.get('pendingRobuxTotal', 0)
            
        except requests.exceptions.RequestException:
            return None
    
    def get_rap(self) -> Optional[int]:
        """Рассчитывает общую стоимость RAP"""
        try:
            total_rap = 0
            cursor = ""
            
            while True:
                params = {'limit': 100, 'sortOrder': 'Asc'}
                if cursor:
                    params['cursor'] = cursor
                
                response = self.session.get(
                    f"{API_ENDPOINTS['inventory']}/v1/users/{self.user_id}/assets/collectibles",
                    params=params,
                    timeout=LONG_REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('data', []):
                    rap_value = item.get('recentAveragePrice', 0)
                    if rap_value:
                        total_rap += rap_value
                
                cursor = data.get('nextPageCursor')
                if not cursor:
                    break
            
            return total_rap
            
        except requests.exceptions.RequestException:
            return None
    
    def get_groups_count(self) -> Optional[int]:
        """Получает количество групп"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['groups']}/v2/users/{self.user_id}/groups/roles",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return len(data.get('data', []))
            
        except requests.exceptions.RequestException:
            return None
    
    def get_badges_info(self) -> Optional[Dict[str, Any]]:
        """Получает информацию о бейджах"""
        try:
            badges_info = {
                'total_count': 0,
                'recent_badges': []
            }
            
            response = self.session.get(
                f"{API_ENDPOINTS['badges']}/v1/users/{self.user_id}/badges",
                params={'limit': 100, 'sortOrder': 'Desc'},
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                badges_info['total_count'] = len(data.get('data', []))
                
                for badge in data.get('data', [])[:5]:
                    badges_info['recent_badges'].append({
                        'name': badge.get('name'),
                        'description': badge.get('description'),
                        'awarded_date': badge.get('statistics', {}).get('awardedDate')
                    })
            
            return badges_info if badges_info['total_count'] > 0 else None
            
        except requests.exceptions.RequestException:
            return None
    
    def check_expensive_items(self) -> Dict[str, bool]:
        """Проверяет владение дорогими предметами"""
        results = {}
        for item_name, (item_type, item_id) in EXPENSIVE_ITEMS.items():
            try:
                response = self.session.get(
                    f"{API_ENDPOINTS['inventory']}/v1/users/{self.user_id}/items/{item_type}/{item_id}/is-owned",
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                results[item_name] = response.json()
            except:
                results[item_name] = False
        
        return results
    
    def get_two_factor_status(self) -> Optional[Dict[str, Any]]:
        """Проверяет статус двухфакторной аутентификации"""
        try:
            twofa_info = {
                'enabled': False,
                'methods': [],
                'pin_enabled': False
            }
            
            # Проверка через metadata
            try:
                response = self.session.get(
                    f"{API_ENDPOINTS['twofa']}/v1/metadata",
                    timeout=REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    twofa_info['enabled'] = data.get('isTwoStepEnabled', False)
            except:
                pass
            
            # Проверка конфигурации
            try:
                response = self.session.get(
                    f"{API_ENDPOINTS['twofa']}/v1/users/{self.user_id}/configuration",
                    timeout=REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    methods = data.get('methods', [])
                    
                    if methods:
                        twofa_info['enabled'] = True
                        for method in methods:
                            method_name = method.get('mediaType', 'Unknown')
                            if method_name == 'Email':
                                twofa_info['methods'].append('📧 Email')
                            elif method_name == 'Authenticator':
                                twofa_info['methods'].append('🔐 Authenticator App')
                            elif method_name == 'SMS':
                                twofa_info['methods'].append('📱 SMS')
                            else:
                                twofa_info['methods'].append(f'🔒 {method_name}')
            except:
                pass
            
            # Проверка PIN кода
            try:
                response = self.session.get(
                    f"{API_ENDPOINTS['auth']}/v1/account/pin",
                    timeout=REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    twofa_info['pin_enabled'] = data.get('isEnabled', False)
            except:
                pass
            
            return twofa_info
            
        except requests.exceptions.RequestException:
            return None
    
    def get_transaction_summary(self) -> Optional[Dict[str, Any]]:
        """Получает сводку транзакций за год и за все время"""
        try:
            summary = {}
            
            # За все время (All-time)
            response_alltime = self.session.get(
                f"{API_ENDPOINTS['economy']}/v2/users/{self.user_id}/transaction-totals",
                params={'timeFrame': 'AllTime', 'transactionType': 'summary'},
                timeout=REQUEST_TIMEOUT
            )
            if response_alltime.status_code == 200:
                data_alltime = response_alltime.json()
                summary['alltime_incoming'] = data_alltime.get('incomingRobuxTotal', 0)
                summary['alltime_outgoing'] = abs(data_alltime.get('outgoingRobuxTotal', 0))
            
            # За год
            response_year = self.session.get(
                f"{API_ENDPOINTS['economy']}/v2/users/{self.user_id}/transaction-totals",
                params={'timeFrame': 'Year', 'transactionType': 'summary'},
                timeout=REQUEST_TIMEOUT
            )
            if response_year.status_code == 200:
                data_year = response_year.json()
                summary['year_incoming'] = data_year.get('incomingRobuxTotal', 0)
                summary['year_outgoing'] = abs(data_year.get('outgoingRobuxTotal', 0))
            
            return summary if summary else None
            
        except requests.exceptions.RequestException:
            return None
    
    def get_robux_sources(self) -> Optional[Dict[str, int]]:
        """Анализирует источники дохода Robux"""
        try:
            sources = {
                'Продажи': 0,
                'Партнерские продажи': 0,
                'Выплаты группы': 0,
                'Другое': 0
            }
            
            response = self.session.get(
                f"{API_ENDPOINTS['economy']}/v2/users/{self.user_id}/transaction-totals",
                params={'timeFrame': 'Year', 'transactionType': 'summary'},
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                sources['Продажи'] = data.get('salesTotal', 0)
                sources['Партнерские продажи'] = data.get('affiliateSalesTotal', 0)
                sources['Выплаты группы'] = data.get('groupPayoutTotal', 0)
                sources['Другое'] = data.get('incomingRobuxTotal', 0) - sum([v for k, v in sources.items() if k != 'Другое'])
            
            return sources if any(sources.values()) else None
            
        except requests.exceptions.RequestException:
            return None
    
    def get_inventory_summary(self) -> Optional[Dict[str, int]]:
        """Получает сводку по инвентарю"""
        try:
            inventory_summary = {
                'Всего предметов': 0,
                'Коллекционные (Limited)': 0,
                'Головные уборы (Hats)': 0,
                'Лица (Faces)': 0,
                'Снаряжение (Gear)': 0,
                'Модели (Models)': 0,
                'Наборы (Bundles)': 0
            }
            
            # Коллекционные предметы
            try:
                response = self.session.get(
                    f"{API_ENDPOINTS['inventory']}/v1/users/{self.user_id}/assets/collectibles",
                    params={'limit': 100, 'sortOrder': 'Asc'},
                    timeout=LONG_REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    count = len(data.get('data', []))
                    inventory_summary['Коллекционные (Limited)'] = count
                    inventory_summary['Всего предметов'] += count
            except:
                pass
            
            # Наборы
            try:
                response = self.session.get(
                    f"{API_ENDPOINTS['catalog']}/v1/users/{self.user_id}/bundles",
                    params={'limit': 100, 'sortOrder': 'Asc'},
                    timeout=LONG_REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    count = len(data.get('data', []))
                    inventory_summary['Наборы (Bundles)'] = count
                    inventory_summary['Всего предметов'] += count
            except:
                pass
            
            # Предметы по типам
            for asset_type_id, category_name in ASSET_TYPES.items():
                try:
                    total_count = 0
                    cursor = ''
                    
                    for _ in range(3):
                        params = {'limit': 100, 'sortOrder': 'Asc'}
                        if cursor:
                            params['cursor'] = cursor
                        
                        response = self.session.get(
                            f"{API_ENDPOINTS['inventory']}/v2/users/{self.user_id}/inventory/{asset_type_id}",
                            params=params,
                            timeout=LONG_REQUEST_TIMEOUT
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            items = data.get('data', [])
                            total_count += len(items)
                            
                            cursor = data.get('nextPageCursor')
                            if not cursor:
                                break
                        else:
                            break
                    
                    if total_count > 0:
                        inventory_summary[category_name] = total_count
                        inventory_summary['Всего предметов'] += total_count
                except:
                    continue
            
            return inventory_summary
            
        except requests.exceptions.RequestException:
            return None
    
    def get_friends_count(self) -> Optional[int]:
        """Получает количество друзей"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['friends']}/v1/users/{self.user_id}/friends/count",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data.get('count', 0)
            
        except requests.exceptions.RequestException:
            return None
    
    def get_followers_count(self) -> Optional[int]:
        """Получает количество подписчиков"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['friends']}/v1/users/{self.user_id}/followers/count",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data.get('count', 0)
            
        except requests.exceptions.RequestException:
            return None
    
    def get_credit_balance(self) -> Optional[float]:
        """Получает кредитный баланс Roblox"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['billing']}/v1/credit",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data.get('balance', 0.0)
            
        except requests.exceptions.RequestException:
            return None
    
    def get_game_purchases(self) -> Optional[Dict[str, Any]]:
        """Анализирует покупки в играх (геймпассы, приват сервера и т.д.)"""
        try:
            game_purchases = {}
            total_spent = 0
            
            # Получаем транзакции
            response = self.session.get(
                f"{API_ENDPOINTS['economy']}/v2/users/{self.user_id}/transactions",
                params={
                    'limit': 100,
                    'transactionType': 'Purchase'
                },
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for transaction in data.get('data', []):
                    # Анализируем описание транзакции
                    details = transaction.get('details', {})
                    name = details.get('name', 'Unknown')
                    amount = abs(transaction.get('currency', {}).get('amount', 0))
                    
                    # Группируем по играм
                    if 'Private Server' in name or 'Gamepass' in name or 'Developer Product' in name:
                        if name not in game_purchases:
                            game_purchases[name] = {
                                'count': 0,
                                'total_spent': 0
                            }
                        
                        game_purchases[name]['count'] += 1
                        game_purchases[name]['total_spent'] += amount
                        total_spent += amount
            
            return {
                'purchases': game_purchases,
                'total_spent': total_spent
            }
            
        except requests.exceptions.RequestException:
            return None
    
    def get_email_info(self) -> Optional[Dict[str, Any]]:
        """Получает информацию о почте (частично скрытую)"""
        try:
            email_info = {
                'email': None,
                'verified': False,
                'domain': None
            }
            
            # Получаем информацию о почте
            response = self.session.get(
                f"{API_ENDPOINTS['account_settings']}/v1/email",
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                email = data.get('emailAddress')
                verified = data.get('verified', False)
                
                email_info['email'] = email
                email_info['verified'] = verified
                
                # Извлекаем домен из частично скрытой почты
                if email and '@' in email:
                    domain = email.split('@')[-1]
                    email_info['domain'] = domain
            
            return email_info
            
        except requests.exceptions.RequestException:
            return None
    
    def get_payment_methods_count(self) -> Optional[int]:
        """Получает количество привязанных карт/методов оплаты"""
        try:
            response = self.session.get(
                f"{API_ENDPOINTS['billing']}/v1/payment-methods",
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                methods = data.get('paymentMethods', [])
                return len(methods)
            
            return 0
            
        except requests.exceptions.RequestException:
            return None
    
    def get_total_inventory_count(self) -> Optional[int]:
        """Получает общее количество предметов в инвентаре (быстрый метод)"""
        try:
            # Используем общий endpoint для всех предметов
            response = self.session.get(
                f"{API_ENDPOINTS['inventory']}/v1/users/{self.user_id}/items/Asset",
                params={'limit': 1},
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('total', 0)
            
            return None
            
        except requests.exceptions.RequestException:
            return None
