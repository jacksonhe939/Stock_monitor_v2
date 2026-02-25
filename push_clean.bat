@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   推送代码到 GitHub
echo ========================================
echo.
echo 注意: 此脚本会删除旧仓库并创建新的
echo       确保你的 API keys 已经从代码中移除！
echo.
pause

:: 删除旧的 git 历史
if exist ".git" (
    echo 删除旧的 Git 历史...
    rmdir /s /q ".git"
)

:: 删除敏感文件
echo 删除敏感文件...
del test_api.py 2>nul
del test_xai.py 2>nul
del test_telegram.py 2>nul
del push_git.py 2>nul
del user_settings.json 2>nul
del config.yaml 2>nul

:: 初始化新仓库
echo 初始化新仓库...
git init
git add .
git commit -m "Stock Noti Beta - AI-powered stock news monitor

Features:
- Interactive Telegram bot with Q&A
- AI-powered news analysis (xAI Grok, OpenAI, etc.)
- User-customizable watchlist
- Adjustable notification intervals
- Multi-language support (zh/en)
- Auto news scheduler
- Deep dive analysis on topics

Commands:
- /add /remove - Manage watchlist
- /watchlist - View settings
- /interval - Set notification interval
- /lang - Set language
- /ask - Ask questions about stocks
- /deep - Deep dive analysis
- /price /news - Stock info"

git branch -M main
git remote add origin https://github.com/jacksonhe939/Stock_monitor_v2.git

echo.
echo 准备推送...
echo 请在 GitHub 上先删除旧仓库（如果存在）
echo 然后创建新的空仓库: Stock_monitor_v2
echo.
pause

git push -u origin main --force

echo.
echo ========================================
echo   ✅ 推送完成！
echo ========================================
echo.
echo 仓库地址: https://github.com/jacksonhe939/Stock_monitor_v2
echo.
pause
