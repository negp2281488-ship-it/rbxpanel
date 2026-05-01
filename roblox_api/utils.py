#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Утилиты для форматирования и вывода
"""

from colorama import Fore, Back, Style, init
from datetime import datetime, timedelta

# Инициализация colorama для Windows
init(autoreset=True)


class ColorPrinter:
    """Класс для цветного вывода в консоль"""
    
    @staticmethod
    def progress(message: str, color=Fore.CYAN):
        """Выводит сообщение с цветом"""
        print(f"{color}⏳ {message}...{Style.RESET_ALL}")
    
    @staticmethod
    def success(message: str):
        """Выводит сообщение об успехе"""
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def error(message: str):
        """Выводит сообщение об ошибке"""
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def warning(message: str):
        """Выводит предупреждение"""
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
    
    @staticmethod
    def info(message: str, color=Fore.WHITE):
        """Выводит информационное сообщение"""
        print(f"{color}{message}{Style.RESET_ALL}")
    
    @staticmethod
    def header(text: str, width: int = 70):
        """Выводит красивый заголовок"""
        print(f"\n{Fore.CYAN}{'='*width}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}{text}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*width}{Style.RESET_ALL}")
    
    @staticmethod
    def separator(width: int = 70):
        """Выводит разделитель"""
        print(f"\n{Fore.CYAN}{'-'*width}{Style.RESET_ALL}")
    
    @staticmethod
    def section_header(text: str, width: int = 70):
        """Выводит заголовок секции"""
        print(f"\n{Fore.CYAN}{'-'*width}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}{text}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-'*width}{Style.RESET_ALL}")
    
    @staticmethod
    def progress_bar(current: int, total: int, width: int = 30) -> str:
        """Создает прогресс-бар"""
        if total == 0:
            return f"{Fore.CYAN}[{'█' * width}]{Style.RESET_ALL}"
        
        percent = current / total
        filled = int(width * percent)
        bar = "█" * filled + "░" * (width - filled)
        return f"{Fore.CYAN}[{bar}]{Style.RESET_ALL}"


class DateFormatter:
    """Класс для форматирования дат"""
    
    @staticmethod
    def format_date(date_str: str) -> str:
        """Форматирует дату в читаемый вид"""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y %H:%M:%S UTC')
        except:
            return date_str
    
    @staticmethod
    def calculate_age(created_date: datetime) -> str:
        """Рассчитывает возраст аккаунта"""
        if not created_date:
            return None
        
        now = datetime.now(created_date.tzinfo)
        age = now - created_date
        
        years = age.days // 365
        months = (age.days % 365) // 30
        days = (age.days % 365) % 30
        
        parts = []
        if years > 0:
            word = 'год' if years == 1 else 'года' if years < 5 else 'лет'
            parts.append(f"{years} {word}")
        if months > 0:
            word = 'месяц' if months == 1 else 'месяца' if months < 5 else 'месяцев'
            parts.append(f"{months} {word}")
        if days > 0 or not parts:
            word = 'день' if days == 1 else 'дня' if days < 5 else 'дней'
            parts.append(f"{days} {word}")
        
        return ", ".join(parts)


class NumberFormatter:
    """Класс для форматирования чисел"""
    
    @staticmethod
    def format_currency(amount: int) -> str:
        """Форматирует число как валюту"""
        return f"{amount:,}".replace(',', ' ')
    
    @staticmethod
    def format_percent(value: float) -> str:
        """Форматирует процент"""
        return f"{value:.1f}%"
