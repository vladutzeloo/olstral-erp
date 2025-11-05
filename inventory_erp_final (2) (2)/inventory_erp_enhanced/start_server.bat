@echo off
echo ============================================
echo Starting Inventory ERP Server...
echo ============================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the Flask application
echo Server starting at http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
echo Default login credentials:
echo Username: admin
echo Password: admin123
echo.
python app.py

pause
