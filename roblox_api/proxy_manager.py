#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Менеджер для работы с прокси
"""

import random
import requests
from typing import Optional, List, Dict
from config import PROXY_FILE, PROXY_CHECK_TIMEOUT, PROXY_TEST_URL
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProxyManager:
    """Класс для управления прокси серверами"""
    
    def __init__(self, proxy_file: str = PROXY_FILE):
        """
        Инициализация менеджера прокси
        
        Args:
            proxy_file: Путь к файлу с прокси
        """
        self.proxy_file = proxy_file
        self.proxies: List[str] = []
        self.working_proxies: List[str] = []
        self._lock = threading.Lock()  # Lock для thread-safe операций
        self.load_proxies()
    
    def load_proxies(self) -> None:
        """Загружает прокси из файла"""
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            logger.info(f"Загружено {len(self.proxies)} прокси из {self.proxy_file}")
        except FileNotFoundError:
            logger.error(f"Файл {self.proxy_file} не найден")
            self.proxies = []
        except Exception as e:
            logger.error(f"Ошибка при загрузке прокси: {e}")
            self.proxies = []
    
    def parse_proxy(self, proxy_string: str) -> Optional[Dict[str, str]]:
        """
        Парсит строку прокси в формате login:password@ip:port
        
        Args:
            proxy_string: Строка с прокси
            
        Returns:
            Словарь с настройками прокси для requests или None
        """
        try:
            # Формат: login:password@ip:port
            if '@' not in proxy_string:
                return None
            
            auth_part, server_part = proxy_string.split('@')
            username, password = auth_part.split(':', 1)
            ip, port = server_part.rsplit(':', 1)
            
            # Формат для requests (SOCKS5)
            proxy_url = f"socks5://{username}:{password}@{ip}:{port}"
            
            return {
                'http': proxy_url,
                'https': proxy_url
            }
        except Exception as e:
            logger.error(f"Ошибка парсинга прокси {proxy_string}: {e}")
            return None
    
    def check_proxy(self, proxy_string: str) -> bool:
        """
        Проверяет работоспособность прокси
        
        Args:
            proxy_string: Строка с прокси
            
        Returns:
            True если прокси работает, False иначе
        """
        proxy_dict = self.parse_proxy(proxy_string)
        if not proxy_dict:
            return False
        
        try:
            response = requests.get(
                PROXY_TEST_URL,
                proxies=proxy_dict,
                timeout=PROXY_CHECK_TIMEOUT
            )
            # Если получили ответ - прокси работает
            if response.status_code in [200, 301, 302, 403]:  # 403 может быть от cloudflare, но прокси работает
                logger.info(f"✓ Прокси работает: {proxy_string.split('@')[1]}")
                return True
            else:
                logger.warning(f"✗ Прокси вернул код {response.status_code}: {proxy_string.split('@')[1]}")
                return False
        except requests.exceptions.Timeout:
            logger.warning(f"✗ Прокси таймаут: {proxy_string.split('@')[1]}")
            return False
        except Exception as e:
            logger.warning(f"✗ Прокси не работает: {proxy_string.split('@')[1]} - {type(e).__name__}")
            return False
    
    def get_random_working_proxy(self, max_attempts: int = 5, force_check: bool = False) -> Optional[Dict[str, str]]:
        """
        Получает случайный рабочий прокси (thread-safe)
        
        Args:
            max_attempts: Максимальное количество попыток найти рабочий прокси
            force_check: Если True, игнорирует кэш и проверяет прокси заново
            
        Returns:
            Словарь с настройками прокси или None
        """
        self._lock.acquire()
        try:
            if not self.proxies:
                logger.error("Список прокси пуст")
                return None
            
            # Если force_check=False и есть кэшированные рабочие прокси, выбираем случайный из них
            if not force_check and self.working_proxies and len(self.working_proxies) > 0:
                # Выбираем случайный из кэшированных рабочих прокси
                proxy_string = random.choice(self.working_proxies)
                proxy_dict = self.parse_proxy(proxy_string)
                
                # Быстрая проверка (без вывода лога) - освобождаем lock на время проверки
                if proxy_dict:
                    # Временно освобождаем lock для проверки по сети
                    self._lock.release()
                    try:
                        response = requests.get(
                            PROXY_TEST_URL,
                            proxies=proxy_dict,
                            timeout=PROXY_CHECK_TIMEOUT
                        )
                        works = response.status_code in [200, 301, 302, 403]
                    except:
                        works = False
                    finally:
                        # Захватываем lock обратно
                        self._lock.acquire()
                    
                    if works:
                        logger.info(f"✓ Использован кэшированный прокси: {proxy_string.split('@')[1]}")
                        return proxy_dict
                    else:
                        # Если прокси не работает, удаляем из кэша
                        logger.warning(f"✗ Прокси из кэша не работает: {proxy_string.split('@')[1]}")
                        if proxy_string in self.working_proxies:
                            self.working_proxies.remove(proxy_string)
            
            # Пробуем найти новый рабочий прокси (случайным образом из всего списка)
            attempts = 0
            tried_proxies = set()
            
            while attempts < max_attempts and len(tried_proxies) < len(self.proxies):
                # Выбираем СЛУЧАЙНЫЙ прокси, который еще не пробовали в этой сессии
                available_proxies = [p for p in self.proxies if p not in tried_proxies]
                if not available_proxies:
                    break
                
                proxy_string = random.choice(available_proxies)
                tried_proxies.add(proxy_string)
                attempts += 1
                
                logger.info(f"Проверка нового прокси {attempts}/{max_attempts}: {proxy_string.split('@')[1]}")
                
                # Временно освобождаем lock для проверки по сети
                self._lock.release()
                try:
                    proxy_works = self.check_proxy(proxy_string)
                finally:
                    self._lock.acquire()
                
                if proxy_works:
                    proxy_dict = self.parse_proxy(proxy_string)
                    if proxy_dict:
                        # Добавляем в кэш рабочих прокси
                        if proxy_string not in self.working_proxies:
                            self.working_proxies.append(proxy_string)
                        return proxy_dict
            
            logger.error(f"Не удалось найти рабочий прокси после {attempts} попыток")
            return None
        finally:
            # Освобождаем lock если он все еще удерживается
            try:
                self._lock.release()
            except RuntimeError:
                # Lock уже освобожден (был return внутри)
                pass
    
    def get_working_proxies_count(self) -> int:
        """Возвращает количество кэшированных рабочих прокси (thread-safe)"""
        with self._lock:
            return len(self.working_proxies)
    
    def clear_working_cache(self) -> None:
        """Очищает кэш рабочих прокси (thread-safe)"""
        with self._lock:
            self.working_proxies.clear()
            logger.info("Кэш рабочих прокси очищен")


# Глобальный экземпляр менеджера прокси
proxy_manager = ProxyManager()

