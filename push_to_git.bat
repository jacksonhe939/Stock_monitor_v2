@echo off
cd /d "C:\Users\jacks\.openclaw\workspace\Stock_Noti_beta"

echo ================================
echo Stock_Noti_beta Git Push Script
echo ================================
echo.

echo [1/6] Initializing git...
git init

echo [2/6] Adding files...
git add .

echo [3/6] Committing...
git commit -m "v2: Add interactive bot, deep analysis, enhanced news format

Features:
- Interactive Q&A bot (python main.py --bot)
- Deep dive analysis on topics
- Enhanced news format with full details
- AI provides risks, opportunities, entry/stop/target
- Questions to consider and catalysts to watch
- Bot commands: /ask, /deep, /price, /news, /stocks"

echo [4/6] Setting branch to main...
git branch -M main

echo [5/6] Adding remote...
git remote remove origin 2>nul
git remote add origin https://github.com/jacksonhe939/Stock_monitor_v2.git

echo [6/6] Pushing to GitHub...
git push -u origin main --force

echo.
echo ================================
echo Done! Check: https://github.com/jacksonhe939/Stock_monitor_v2
echo ================================
pause
