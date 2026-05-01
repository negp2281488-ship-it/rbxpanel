@echo off
chcp 65001 >nul
title RBXPanel API Server
color 0B

cd /d "%~dp0roblox_api"

echo ================================================
echo    RBXPanel API Server
echo    Port: 8081
echo ================================================
echo.

python flask_api.py

pause

