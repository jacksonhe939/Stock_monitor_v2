@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo   Stock_Noti_beta - Configuration
echo ========================================
echo.

echo Please follow the prompts to configure.
echo (Press Enter to keep current value)
echo.

:: AI Provider
echo [1/5] Select AI Provider:
echo   1. xAI (Grok) - Recommended
echo   2. OpenAI
echo   3. Zhipu (GLM)
echo   4. DeepSeek
echo.
set /p provider_choice="Select (1-4) [default 1]: "

if "%provider_choice%"=="" set provider_choice=1
if "%provider_choice%"=="1" (
    set provider=xai
    set model=grok-4-latest
    set base_url=https://api.x.ai/v1
    set key_prompt=xAI API Key (format: xai-xxx)
)
if "%provider_choice%"=="2" (
    set provider=openai
    set model=gpt-4o-mini
    set base_url=https://api.openai.com/v1
    set key_prompt=OpenAI API Key (format: sk-xxx)
)
if "%provider_choice%"=="3" (
    set provider=zhipu
    set model=glm-4-flash
    set base_url=https://open.bigmodel.cn/api/paas/v4
    set key_prompt=Zhipu API Key
)
if "%provider_choice%"=="4" (
    set provider=deepseek
    set model=deepseek-chat
    set base_url=https://api.deepseek.com/v1
    set key_prompt=DeepSeek API Key
)

echo.
echo [2/5] Enter API Key
echo %key_prompt%
set /p api_key="API Key: "

echo.
echo [3/5] Telegram Bot Token
echo Get from @BotFather (format: 123456789:ABCdef...)
set /p bot_token="Bot Token: "

echo.
echo [4/5] Telegram Chat ID
echo Message your bot, then visit api.telegram.org/bot^<TOKEN^>/getUpdates
set /p chat_id="Chat ID: "

echo.
echo [5/5] Default stocks to monitor (comma-separated, e.g. NVDA,AAPL,TSLA)
set /p stocks="Symbols: "

if "%stocks%"=="" set stocks=NVDA,LUNR

:: Write config file
echo # Stock_Noti_beta Configuration > config.yaml
echo. >> config.yaml
echo ai: >> config.yaml
echo   provider: "%provider%" >> config.yaml
echo   api_key: "%api_key%" >> config.yaml
echo   model: "%model%" >> config.yaml
echo   base_url: "%base_url%" >> config.yaml
echo. >> config.yaml
echo telegram: >> config.yaml
echo   bot_token: "%bot_token%" >> config.yaml
echo   chat_id: "%chat_id%" >> config.yaml
echo. >> config.yaml
echo stocks: >> config.yaml
for %%s in (%stocks:,= %) do (
    echo   - symbol: "%%s" >> config.yaml
    echo     name: "%%s" >> config.yaml
    echo     keywords: [] >> config.yaml
)
echo. >> config.yaml
echo alert_settings: >> config.yaml
echo   interval_minutes: 5 >> config.yaml
echo   min_importance: 5 >> config.yaml
echo   price_change_threshold: 3.0 >> config.yaml
echo   news_timeframe_hours: 24 >> config.yaml
echo. >> config.yaml
echo schedule: >> config.yaml
echo   enabled: false >> config.yaml
echo   cron: "0 9-16 * * 1-5" >> config.yaml
echo   timezone: "America/New_York" >> config.yaml
echo. >> config.yaml
echo logging: >> config.yaml
echo   level: "INFO" >> config.yaml
echo   file: "logs/stock_noti.log" >> config.yaml

echo.
echo ========================================
echo   Configuration saved!
echo ========================================
echo.
echo Config saved to: config.yaml
echo.
echo Next: Run start.bat to start the bot
echo.
pause
