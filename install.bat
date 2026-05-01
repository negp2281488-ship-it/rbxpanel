@echo off
chcp 65001 >nul
title RBXPanel - Установка зависимостей
color 0E

echo ================================================
echo    RBXPanel - Установка зависимостей
echo ================================================
echo.

cd /d "%~dp0"

echo [1/2] Проверка Python...
python --version
if errorlevel 1 (
    echo [ОШИБКА] Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)
echo [OK] Python установлен
echo.

echo [2/2] Установка зависимостей...
echo.

echo Установка зависимостей для основного приложения (site)...
cd site
pip install -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости для site
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo Установка зависимостей для API (roblox_api)...
cd roblox_api
pip install -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости для roblox_api
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo ================================================
echo    Установка завершена!
echo ================================================
echo.
pause

