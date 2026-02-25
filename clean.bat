@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo   Clean Private Data
echo ========================================
echo.

echo Removing files with private info...

:: Delete test files (may contain API keys)
del /q test_*.py 2>nul
del /q push_git.py 2>nul
del /q git_push_log.txt 2>nul

:: Delete config files with API keys
del /q config.yaml 2>nul
del /q user_settings.json 2>nul

:: Delete logs
rmdir /s /q logs 2>nul

:: Delete Python cache
rmdir /s /q __pycache__ 2>nul
rmdir /s /q modules\__pycache__ 2>nul

:: Delete old git history
rmdir /s /q .git 2>nul

echo.
echo ========================================
echo   Done! Private files removed.
echo ========================================
echo.

echo Files ready for GitHub:
echo   - config.example.yaml (template only)
echo   - All source code
echo   - No API keys or personal info
echo.

echo Next step: Run push_github.bat to upload
echo.
pause
