@echo off
chcp 65001 >nul
title RBXPanel — Запуск
color 0A

cd /d "%~dp0"

echo.
echo  ══════════════════════════════════════════
echo      RBXPanel — Запуск всех серверов
echo  ══════════════════════════════════════════
echo.

:: ─── Проверка Python ──────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден! Установите Python 3.10+
    pause & exit /b 1
)

:: ─── Установка зависимостей ───────────────────────────────────
echo [1/4] Установка зависимостей...
echo.

echo   roblox_api...
cd "%~dp0roblox_api"
pip install -q -r requirements.txt
if errorlevel 1 ( echo [ERR] roblox_api & pause & exit /b 1 )

echo   site...
cd "%~dp0site"
pip install -q -r requirements.txt
if errorlevel 1 ( echo [ERR] site & pause & exit /b 1 )

cd /d "%~dp0"
echo [OK] Зависимости установлены
echo.

:: ─── Запуск серверов ──────────────────────────────────────────
echo [2/4] Roblox API (порт 8081)...
start "RBX — API :8081" cmd /k "cd /d %~dp0roblox_api && python flask_api.py"
timeout /t 3 /nobreak >nul

echo [3/4] Site (порт 80 или 5000)...
start "RBX — Site :80" cmd /k "cd /d %~dp0site && python app.py"
timeout /t 2 /nobreak >nul

echo.
echo  ══════════════════════════════════════════
echo.
echo   Roblox API   ^>  http://localhost:8081
echo   Site         ^>  http://localhost:80
echo.
echo   Закрой нужные окна чтобы остановить серверы
echo.
pause

