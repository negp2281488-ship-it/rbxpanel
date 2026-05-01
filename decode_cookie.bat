@echo off
chcp 65001 >nul
title RBXPanel - Decode Cookie
color 0C

cd /d "%~dp0site"

echo ================================================
echo    RBXPanel - Cookie Decoder
echo ================================================
echo.

if "%1"=="" (
    echo Использование:
    echo   decode_cookie.bat "зашифрованная_cookie"
    echo   decode_cookie.bat --interactive
    echo   decode_cookie.bat --file cookies\123.txt
    echo.
    python decode_cookie.py --help
) else (
    python decode_cookie.py %*
)

echo.
pause

