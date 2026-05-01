#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Массовая проверка Roblox cookies
Поддерживает проверку большого количества аккаунтов с многопоточностью
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from colorama import Fore, Style
from api_client import RobloxAPI
from utils import ColorPrinter, NumberFormatter
import time


class CookieChecker:
    """Класс для массовой проверки cookies"""
    
    def __init__(self, max_workers: int = 10):
        """
        Инициализация
        
        Args:
            max_workers: Количество потоков для параллельной проверки
        """
        self.max_workers = max_workers
        self.printer = ColorPrinter()
        self.lock = Lock()
        
        # Счетчики
        self.total = 0
        self.checked = 0
        self.valid = 0
        self.invalid = 0
        
        # Результаты
        self.valid_accounts = []
        self.invalid_cookies = []
    
    def check_single_cookie(self, cookie: str, index: int) -> Dict[str, Any]:
        """
        Проверяет один cookie
        
        Args:
            cookie: Cookie для проверки
            index: Номер cookie в списке
        
        Returns:
            Dict: Результат проверки
        """
        result = {
            'index': index,
            'cookie': cookie[:50] + "..." if len(cookie) > 50 else cookie,
            'full_cookie': cookie,
            'valid': False,
            'data': None,
            'error': None
        }
        
        try:
            api = RobloxAPI(cookie)
            
            # Проверка аутентификации
            if not api.get_authenticated_user():
                result['error'] = 'Invalid or expired cookie'
                return result
            
            # Получаем базовую информацию
            result['valid'] = True
            
            # Собираем данные
            data = {
                'user_id': api.user_id,
                'username': api.username,
                'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Дополнительная информация (опционально)
            try:
                user_details = api.get_user_details()
                if user_details:
                    data['created'] = user_details.get('created')
                
                balance = api.get_robux_balance()
                if balance is not None:
                    data['robux'] = balance
                
                premium = api.get_premium_status()
                if premium is not None:
                    data['premium'] = premium
                
                location = api.get_account_location()
                if location:
                    data['location'] = location
                
                groups = api.get_groups_count()
                if groups is not None:
                    data['groups'] = groups
                
            except:
                pass  # Если не получили доп. данные, продолжаем
            
            result['data'] = data
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def check_cookies_batch(self, cookies: List[str], delay: float = 0.5) -> None:
        """
        Проверяет список cookies с многопоточностью
        
        Args:
            cookies: Список cookies для проверки
            delay: Задержка между запросами (секунды)
        """
        self.total = len(cookies)
        self.checked = 0
        self.valid = 0
        self.invalid = 0
        
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}🔍 МАССОВАЯ ПРОВЕРКА COOKIES{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.GREEN}📊 Всего cookies для проверки:{Style.RESET_ALL} {Fore.YELLOW}{self.total}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}⚙️  Потоков:{Style.RESET_ALL} {Fore.CYAN}{self.max_workers}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}⏱️  Задержка:{Style.RESET_ALL} {Fore.CYAN}{delay}с{Style.RESET_ALL}\n")
        
        start_time = time.time()
        
        # Многопоточная проверка
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Создаем задачи
            futures = {
                executor.submit(self.check_single_cookie, cookie, i): i 
                for i, cookie in enumerate(cookies, 1)
            }
            
            # Обрабатываем результаты по мере готовности
            for future in as_completed(futures):
                result = future.result()
                
                with self.lock:
                    self.checked += 1
                    
                    if result['valid']:
                        self.valid += 1
                        self.valid_accounts.append(result)
                        status = f"{Fore.GREEN}✅ VALID{Style.RESET_ALL}"
                        username = result['data'].get('username', 'Unknown')
                        user_id = result['data'].get('user_id', 'Unknown')
                        robux = result['data'].get('robux', 'N/A')
                        
                        print(f"{Fore.CYAN}[{self.checked}/{self.total}]{Style.RESET_ALL} {status} - "
                              f"{Fore.WHITE}{username}{Style.RESET_ALL} "
                              f"(ID: {Fore.YELLOW}{user_id}{Style.RESET_ALL}, "
                              f"💰 {Fore.YELLOW}{robux}{Style.RESET_ALL} R$)")
                    else:
                        self.invalid += 1
                        self.invalid_cookies.append(result)
                        status = f"{Fore.RED}❌ INVALID{Style.RESET_ALL}"
                        error = result.get('error', 'Unknown error')
                        
                        print(f"{Fore.CYAN}[{self.checked}/{self.total}]{Style.RESET_ALL} {status} - "
                              f"{Fore.RED}{error}{Style.RESET_ALL}")
                    
                    # Прогресс
                    percent = (self.checked / self.total) * 100
                    bar = self._create_progress_bar(self.checked, self.total)
                    print(f"{Fore.CYAN}{bar} {percent:.1f}%{Style.RESET_ALL}\n")
                
                # Задержка между запросами
                if delay > 0:
                    time.sleep(delay)
        
        elapsed_time = time.time() - start_time
        
        # Итоговая статистика
        self._print_summary(elapsed_time)
    
    def _create_progress_bar(self, current: int, total: int, width: int = 40) -> str:
        """Создает прогресс-бар"""
        if total == 0:
            return f"[{'█' * width}]"
        
        filled = int(width * (current / total))
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
    
    def _print_summary(self, elapsed_time: float):
        """Выводит итоговую статистику"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}📊 ИТОГОВАЯ СТАТИСТИКА{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.WHITE}Всего проверено:{Style.RESET_ALL} {Fore.CYAN}{self.checked}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Валидных:{Style.RESET_ALL} {Fore.GREEN}{self.valid}{Style.RESET_ALL} "
              f"({(self.valid/self.total*100):.1f}%)")
        print(f"{Fore.RED}❌ Невалидных:{Style.RESET_ALL} {Fore.RED}{self.invalid}{Style.RESET_ALL} "
              f"({(self.invalid/self.total*100):.1f}%)")
        print(f"{Fore.CYAN}⏱️  Время:{Style.RESET_ALL} {Fore.YELLOW}{elapsed_time:.2f}с{Style.RESET_ALL}")
        print(f"{Fore.CYAN}⚡ Скорость:{Style.RESET_ALL} {Fore.YELLOW}{(self.total/elapsed_time):.2f}{Style.RESET_ALL} cookies/сек")
        
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    def save_results(self, output_dir: str = "results") -> None:
        """
        Сохраняет результаты в файлы
        
        Args:
            output_dir: Папка для сохранения результатов
        """
        import os
        
        # Создаем папку если не существует
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Сохраняем валидные аккаунты
        if self.valid_accounts:
            # JSON
            valid_json = os.path.join(output_dir, f'valid_accounts_{timestamp}.json')
            with open(valid_json, 'w', encoding='utf-8') as f:
                json.dump(self.valid_accounts, f, indent=2, ensure_ascii=False)
            
            # CSV
            valid_csv = os.path.join(output_dir, f'valid_accounts_{timestamp}.csv')
            with open(valid_csv, 'w', newline='', encoding='utf-8') as f:
                if self.valid_accounts:
                    # Определяем все возможные поля
                    fieldnames = ['index', 'cookie', 'full_cookie']
                    if self.valid_accounts[0]['data']:
                        fieldnames.extend(self.valid_accounts[0]['data'].keys())
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for acc in self.valid_accounts:
                        row = {
                            'index': acc['index'],
                            'cookie': acc['cookie'],
                            'full_cookie': acc['full_cookie']
                        }
                        if acc['data']:
                            row.update(acc['data'])
                        writer.writerow(row)
            
            # TXT (простой формат)
            valid_txt = os.path.join(output_dir, f'valid_cookies_{timestamp}.txt')
            with open(valid_txt, 'w', encoding='utf-8') as f:
                for acc in self.valid_accounts:
                    f.write(f"{acc['full_cookie']}\n")
            
            self.printer.success(f"Валидные аккаунты сохранены:")
            print(f"   📄 JSON: {Fore.CYAN}{valid_json}{Style.RESET_ALL}")
            print(f"   📊 CSV:  {Fore.CYAN}{valid_csv}{Style.RESET_ALL}")
            print(f"   📝 TXT:  {Fore.CYAN}{valid_txt}{Style.RESET_ALL}")
        
        # Сохраняем невалидные cookies
        if self.invalid_cookies:
            invalid_json = os.path.join(output_dir, f'invalid_cookies_{timestamp}.json')
            with open(invalid_json, 'w', encoding='utf-8') as f:
                json.dump(self.invalid_cookies, f, indent=2, ensure_ascii=False)
            
            invalid_txt = os.path.join(output_dir, f'invalid_cookies_{timestamp}.txt')
            with open(invalid_txt, 'w', encoding='utf-8') as f:
                for cookie in self.invalid_cookies:
                    f.write(f"{cookie['full_cookie']} # {cookie.get('error', 'Unknown')}\n")
            
            self.printer.warning(f"Невалидные cookies сохранены:")
            print(f"   📄 JSON: {Fore.CYAN}{invalid_json}{Style.RESET_ALL}")
            print(f"   📝 TXT:  {Fore.CYAN}{invalid_txt}{Style.RESET_ALL}")
        
        # Сводный отчет
        summary_file = os.path.join(output_dir, f'summary_{timestamp}.txt')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"ОТЧЕТ О ПРОВЕРКЕ ROBLOX COOKIES\n")
            f.write(f"{'='*70}\n\n")
            f.write(f"Дата проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего проверено: {self.checked}\n")
            f.write(f"Валидных: {self.valid} ({(self.valid/self.total*100):.1f}%)\n")
            f.write(f"Невалидных: {self.invalid} ({(self.invalid/self.total*100):.1f}%)\n\n")
            
            if self.valid_accounts:
                f.write(f"\nВАЛИДНЫЕ АККАУНТЫ:\n")
                f.write(f"{'-'*70}\n")
                for acc in self.valid_accounts:
                    data = acc['data']
                    f.write(f"\n[{acc['index']}] {data.get('username', 'Unknown')}\n")
                    f.write(f"  User ID: {data.get('user_id', 'N/A')}\n")
                    f.write(f"  Robux: {data.get('robux', 'N/A')}\n")
                    f.write(f"  Premium: {'Yes' if data.get('premium') else 'No'}\n")
                    f.write(f"  Location: {data.get('location', 'N/A')}\n")
                    f.write(f"  Groups: {data.get('groups', 'N/A')}\n")
        
        self.printer.success(f"Сводный отчет: {Fore.CYAN}{summary_file}{Style.RESET_ALL}")


def load_cookies_from_file(filename: str) -> List[str]:
    """
    Загружает cookies из файла
    
    Args:
        filename: Имя файла
    
    Returns:
        List[str]: Список cookies
    """
    cookies = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем пустые строки и комментарии
                if line and not line.startswith('#'):
                    # Если строка содержит комментарий, берем только cookie
                    cookie = line.split('#')[0].strip()
                    if cookie:
                        cookies.append(cookie)
        
        return cookies
    
    except FileNotFoundError:
        print(f"{Fore.RED}❌ Файл {filename} не найден!{Style.RESET_ALL}")
        return []
    except Exception as e:
        print(f"{Fore.RED}❌ Ошибка чтения файла: {e}{Style.RESET_ALL}")
        return []


def main():
    """Главная функция для массовой проверки"""
    
    printer = ColorPrinter()
    
    printer.header("🔍 МАССОВАЯ ПРОВЕРКА ROBLOX COOKIES", 70)
    
    print(f"\n{Fore.CYAN}Этот скрипт проверяет большое количество cookies")
    print(f"и сохраняет результаты в отдельные файлы.{Style.RESET_ALL}\n")
    
    # Выбор режима
    print(f"{Fore.YELLOW}Выберите режим:{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}1.{Style.RESET_ALL} Загрузить из файла")
    print(f"  {Fore.CYAN}2.{Style.RESET_ALL} Ввести вручную (через запятую)")
    
    choice = input(f"\n{Fore.GREEN}Ваш выбор (1/2):{Style.RESET_ALL} ").strip()
    
    cookies = []
    
    if choice == '1':
        filename = input(f"{Fore.GREEN}Имя файла с cookies:{Style.RESET_ALL} ").strip()
        if not filename:
            filename = "cookies.txt"
        
        cookies = load_cookies_from_file(filename)
        
        if not cookies:
            printer.error("Не удалось загрузить cookies из файла")
            return
    
    elif choice == '2':
        print(f"{Fore.YELLOW}Введите cookies (через запятую или каждый с новой строки):{Style.RESET_ALL}")
        print(f"{Fore.CYAN}(Нажмите Enter дважды для завершения ввода){Style.RESET_ALL}\n")
        
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        
        # Парсим cookies
        text = ' '.join(lines)
        cookies = [c.strip() for c in text.replace(',', '\n').split('\n') if c.strip()]
    
    else:
        printer.error("Неверный выбор!")
        return
    
    if not cookies:
        printer.error("Не найдено cookies для проверки!")
        return
    
    # Настройки проверки
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Настройки проверки:{Style.RESET_ALL}\n")
    
    threads_input = input(f"{Fore.GREEN}Количество потоков (по умолчанию 10):{Style.RESET_ALL} ").strip()
    threads = int(threads_input) if threads_input.isdigit() else 10
    
    delay_input = input(f"{Fore.GREEN}Задержка между запросами в секундах (по умолчанию 0.5):{Style.RESET_ALL} ").strip()
    delay = float(delay_input) if delay_input else 0.5
    
    # Создаем checker и запускаем проверку
    checker = CookieChecker(max_workers=threads)
    checker.check_cookies_batch(cookies, delay=delay)
    
    # Сохранение результатов
    save = input(f"\n{Fore.GREEN}Сохранить результаты? (y/n):{Style.RESET_ALL} ").strip().lower()
    
    if save == 'y' or save == 'yes' or save == '':
        output_dir = input(f"{Fore.GREEN}Папка для сохранения (по умолчанию 'results'):{Style.RESET_ALL} ").strip()
        if not output_dir:
            output_dir = "results"
        
        checker.save_results(output_dir)
        printer.success("Результаты успешно сохранены!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  Проверка прервана пользователем.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Критическая ошибка: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
