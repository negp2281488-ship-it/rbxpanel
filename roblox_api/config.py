#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Конфигурация для Roblox Profile Checker
"""

# Настройки таймаутов (в секундах)
REQUEST_TIMEOUT = 10  # Таймаут для обычных запросов
LONG_REQUEST_TIMEOUT = 30  # Таймаут для долгих операций (например, инвентарь)

# Настройки прокси
PROXY_FILE = 'proxies.txt'  # Файл с прокси
PROXY_CHECK_TIMEOUT = 5  # Таймаут для проверки прокси
PROXY_TEST_URL = 'https://www.roblox.com/'  # URL для проверки прокси

# API эндпоинты Roblox
API_ENDPOINTS = {
    'users': 'https://users.roblox.com',
    'auth': 'https://auth.roblox.com',
    'economy': 'https://economy.roblox.com',
    'inventory': 'https://inventory.roblox.com',
    'groups': 'https://groups.roblox.com',
    'friends': 'https://friends.roblox.com',
    'badges': 'https://badges.roblox.com',
    'presence': 'https://presence.roblox.com',
    'premium': 'https://premiumfeatures.roblox.com',
    'billing': 'https://billing.roblox.com',
    'catalog': 'https://catalog.roblox.com',
    'twofa': 'https://twostepverification.roblox.com',
    'account_settings': 'https://accountsettings.roblox.com'
}

# Дорогие предметы для проверки
EXPENSIVE_ITEMS = {
    'Korblox Deathspeaker': ('Bundle', 139607770),
    'Headless Horseman': ('Bundle', 108158379),
}

# Типы активов для инвентаря (только основные для быстрой проверки)
ASSET_TYPES = {
    8: 'Головные уборы (Hats)',
    18: 'Лица (Faces)',
    19: 'Снаряжение (Gear)',
    41: 'Прически (Hair)',
    42: 'Аксессуары на лицо (Face Acc)',
    43: 'Аксессуары на шею (Neck Acc)',
    44: 'Аксессуары на плечо (Shoulder Acc)',
    45: 'Передние аксессуары (Front Acc)',
    46: 'Задние аксессуары (Back Acc)',
    47: 'Аксессуары на талию (Waist Acc)',
}

# Коды стран с флагами
COUNTRY_NAMES = {
    'US': '🇺🇸 США (United States)',
    'RU': '🇷🇺 Россия (Russia)',
    'GB': '🇬🇧 Великобритания (United Kingdom)',
    'CA': '🇨🇦 Канада (Canada)',
    'AU': '🇦🇺 Австралия (Australia)',
    'DE': '🇩🇪 Германия (Germany)',
    'FR': '🇫🇷 Франция (France)',
    'BR': '🇧🇷 Бразилия (Brazil)',
    'MX': '🇲🇽 Мексика (Mexico)',
    'ES': '🇪🇸 Испания (Spain)',
    'IT': '🇮🇹 Италия (Italy)',
    'PL': '🇵🇱 Польша (Poland)',
    'UA': '🇺🇦 Украина (Ukraine)',
    'TR': '🇹🇷 Турция (Turkey)',
    'NL': '🇳🇱 Нидерланды (Netherlands)',
    'SE': '🇸🇪 Швеция (Sweden)',
    'JP': '🇯🇵 Япония (Japan)',
    'KR': '🇰🇷 Южная Корея (South Korea)',
    'CN': '🇨🇳 Китай (China)',
    'IN': '🇮🇳 Индия (India)',
    'PH': '🇵🇭 Филиппины (Philippines)',
    'VN': '🇻🇳 Вьетнам (Vietnam)',
    'ID': '🇮🇩 Индонезия (Indonesia)',
    'MY': '🇲🇾 Малайзия (Malaysia)',
    'SG': '🇸🇬 Сингапур (Singapore)',
    'TH': '🇹🇭 Таиланд (Thailand)',
    'AR': '🇦🇷 Аргентина (Argentina)',
    'CL': '🇨🇱 Чили (Chile)',
    'CO': '🇨🇴 Колумбия (Colombia)',
    'PE': '🇵🇪 Перу (Peru)',
    'BY': '🇧🇾 Беларусь (Belarus)',
    'KZ': '🇰🇿 Казахстан (Kazakhstan)',
}

# Типы транзакций
TRANSACTION_TYPES = [
    ('Sale', 'Продажа'),
    ('Purchase', 'Покупка'),
    ('AffiliateSale', 'Партнерская продажа'),
    ('DevEx', 'DevEx'),
    ('GroupPayout', 'Выплата группы'),
    ('AdSpend', 'Расходы на рекламу')
]
