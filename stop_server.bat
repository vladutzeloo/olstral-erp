@echo off
echo ============================================
echo Stopping Inventory ERP Server...
echo ============================================
echo.

REM Kill any Python processes running Flask
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *flask*" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *app.py*" >nul 2>&1

echo Server stopped.
echo.
pause
