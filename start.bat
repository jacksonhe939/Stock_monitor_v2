@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo   Stock_Noti_beta - AI Stock Monitor
echo ========================================
echo.

:: Check config
if not exist "config.yaml" (
    echo [ERROR] Config file not found!
    echo.
    echo Please run config.bat first to set up your API keys.
    echo.
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Checking dependencies...
pip install yfinance pyyaml pydantic requests openai -q 2>nul

:: Test connections
echo [2/3] Testing connections...
python main.py --test --quiet 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Connection test failed!
    echo Please run config.bat to check your settings.
    echo.
    pause
    exit /b 1
)

echo [OK] Connections working
echo.

:: Start service
echo [3/3] Starting service...
echo.
echo Bot is running! Send /help to Telegram for instructions.
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python main.py --bot --send-help

pause
