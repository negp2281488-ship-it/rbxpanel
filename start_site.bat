@echo off
chcp 65001 >nul
title RBXPanel Main Server
color 0A

cd /d "%~dp0site"

echo ================================================
echo    RBXPanel Main Server
echo    Port: 80
echo ================================================
echo.

python app.py

pause

