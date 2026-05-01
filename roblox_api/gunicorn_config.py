#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gunicorn конфигурация для production
"""

import multiprocessing

# Биндинг
bind = "0.0.0.0:8081"

# Workers
# Рекомендуется: (2 x $num_cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Максимум 20 workers (можно настроить под свою нагрузку)
if workers > 20:
    workers = 20

# Тип worker - gevent для асинхронной обработки
worker_class = "gevent"

# Количество одновременных подключений на worker
worker_connections = 1000

# Таймауты
timeout = 120  # 2 минуты на обработку запроса
keepalive = 5

# Логирование
accesslog = "-"  # STDOUT
errorlog = "-"   # STDERR
loglevel = "info"

# Preload приложения
preload_app = False  # False чтобы каждый worker загружал свои прокси

# Перезапуск workers
max_requests = 1000  # Перезапуск worker после 1000 запросов
max_requests_jitter = 100  # Случайный jitter для избежания одновременного перезапуска

# Graceful timeout
graceful_timeout = 30

# Daemon mode (False для контейнеров/systemd)
daemon = False

print(f"🚀 Gunicorn запускается с {workers} workers (gevent)")
print(f"📡 Каждый worker может обрабатывать до {worker_connections} соединений")
print(f"⚡ Общая пропускная способность: ~{workers * worker_connections} одновременных запросов")

