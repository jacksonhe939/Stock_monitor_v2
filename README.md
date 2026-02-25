# Stock_Noti_beta

🤖 AI-powered stock news monitor with Telegram bot. Get intelligent news analysis, price alerts, and interactive Q&A.

## Features

- 📊 **Real-time stock data** from Yahoo Finance
- 🤖 **AI-powered analysis** with xAI Grok, OpenAI, and more
- 📱 **Telegram bot** for interactive Q&A
- ⚙️ **User customization** - watchlist, intervals, language
- ⏰ **Auto news scheduler** - periodic updates
- 🔍 **Deep dive analysis** on specific topics

## Quick Start

### 1. Configure

Double-click `config.bat` and follow the prompts to set up:
- AI API key (xAI, OpenAI, etc.)
- Telegram bot token (from @BotFather)
- Telegram chat ID

### 2. Start

Double-click `start.bat` to launch the bot.

### 3. Use

Send `/help` to your Telegram bot to see all commands!

## Commands Reference

### 📊 Watchlist Management

| Command | Description | Example |
|---------|-------------|---------|
| `/watchlist` | View your settings | `/watchlist` |
| `/add <symbol>` | Add stock to watchlist | `/add TSLA` |
| `/remove <symbol>` | Remove from watchlist | `/remove TSLA` |
| `/interval <min>` | Set update interval | `/interval 30` |
| `/lang zh` or `/lang en` | Set language | `/lang zh` |

### 📈 Stock Information

| Command | Description | Example |
|---------|-------------|---------|
| `/stocks` | View all monitored stocks | `/stocks` |
| `/price <symbol>` | Get current price | `/price NVDA` |
| `/news <symbol>` | Get latest news | `/news TSLA` |

### 🤖 AI Analysis

| Command | Description | Example |
|---------|-------------|---------|
| `/ask <symbol> <question>` | Ask any question | `/ask NVDA 财报前应该买入吗？` |
| `/deep <symbol> <topic>` | Deep dive analysis | `/deep LUNR NASA合同` |

### 💬 Direct Questions

You can also just type your question directly:
- "NVDA的财报怎么样？"
- "为什么TSLA跌了？"

## File Structure

```
Stock_Noti_beta/
├── config.bat          # Configuration wizard
├── start.bat           # Start the bot
├── push_clean.bat      # Push to GitHub (clean)
├── main.py             # Entry point
├── config.example.yaml # Configuration template
├── config.yaml         # Your config (gitignored)
├── user_settings.json  # User settings (gitignored)
└── modules/
    ├── config_loader.py
    ├── stock_fetcher.py
    ├── news_analyzer.py
    ├── telegram_notifier.py
    ├── interactive_bot.py
    └── user_settings.py
```

## Supported AI Providers

| Provider | API Key Source | Models |
|----------|---------------|--------|
| xAI | x.ai | grok-4-latest |
| OpenAI | platform.openai.com | gpt-4o-mini |
| 智谱 | open.bigmodel.cn | glm-4-flash |
| DeepSeek | platform.deepseek.com | deepseek-chat |

## Getting Telegram Credentials

1. **Bot Token**: Message [@BotFather](https://t.me/BotFather) → `/newbot` → Copy token
2. **Chat ID**: 
   - Message your bot
   - Visit `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find `"chat":{"id":YOUR_CHAT_ID}`

## Push to GitHub

To push a clean version (without API keys):

1. Make sure `config.yaml` has placeholder values
2. Delete old repository on GitHub
3. Run `push_clean.bat`

## License

MIT
