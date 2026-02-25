@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo   Clean and Push to GitHub
echo ========================================
echo.
echo WARNING: This will:
echo   - Delete all files with API keys
echo   - Delete test files
echo   - Delete old git history
echo   - Create fresh clean repository
echo.
echo Your API keys will be saved in backup folder.
echo.
pause

:: Create backup folder
if not exist "backup" mkdir backup

:: Backup config files
echo [1/5] Backing up config files...
if exist "config.yaml" (
    copy "config.yaml" "backup\config.yaml.bak" >nul 2>&1
    del "config.yaml"
)
if exist "user_settings.json" (
    copy "user_settings.json" "backup\user_settings.json.bak" >nul 2>&1
    del "user_settings.json"
)

:: Delete test files
echo [2/5] Removing test files...
del /q test_*.py 2>nul
del /q push_git.py 2>nul
del /q check_files.py 2>nul
del /q git_push_log.txt 2>nul

:: Delete cache and logs
echo [3/5] Cleaning cache and logs...
rmdir /s /q logs 2>nul
rmdir /s /q __pycache__ 2>nul
rmdir /s /q modules\__pycache__ 2>nul

:: Delete old git history
echo [4/5] Removing old git history...
rmdir /s /q .git 2>nul

:: Create new repository
echo [5/5] Creating clean repository...
git init
git add .
git commit -m "Stock Noti Beta - AI Stock News Monitor

Features:
- Interactive Telegram bot with Q&A
- AI-powered news analysis (xAI, OpenAI, etc.)
- User-customizable watchlist
- Auto news scheduler with intervals
- Multi-language support (zh/en)
- Clickable news links
- Deep dive analysis

Setup:
1. Run config.bat to configure API keys
2. Run start.bat to start the bot"

git branch -M main

echo.
echo ========================================
echo   Ready to push!
echo ========================================
echo.
echo IMPORTANT: 
echo   1. Go to GitHub and DELETE old repository
echo   2. Create NEW empty repository: Stock_monitor_v2
echo   3. Press any key to push
echo.
pause

git remote add origin https://github.com/jacksonhe939/Stock_monitor_v2.git
git push -u origin main --force

if errorlevel 1 (
    echo.
    echo Push failed. Check:
    echo   - Old repo deleted on GitHub
    echo   - New empty repo created
) else (
    echo.
    echo SUCCESS!
    echo Repository: https://github.com/jacksonhe939/Stock_monitor_v2
)

echo.
echo Your API keys are backed up in: backup/
echo.
pause
