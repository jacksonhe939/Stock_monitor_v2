"""
Interactive Telegram Bot for Q&A about stocks and news
"""
import requests
import json
import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging

from .user_settings import UserSettings

logger = logging.getLogger(__name__)


class InteractiveBot:
    """Telegram bot that can receive and respond to user questions"""

    def __init__(
        self,
        bot_token: str,
        analyzer,  # NewsAnalyzer instance
        fetcher,   # StockFetcher instance
        config,
    ):
        self.bot_token = bot_token
        self.analyzer = analyzer
        self.fetcher = fetcher
        self.config = config
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0

        # User settings
        self.user_settings = UserSettings()

        # Store recent alerts for context
        self.recent_alerts: Dict[str, Dict[str, Any]] = {}
        self.recent_news: Dict[str, list] = {}

        # Auto news scheduler
        self.scheduler_running = False
        self.scheduler_thread = None

        # Processed messages to avoid duplicates
        self.processed_messages = set()

        # Command handlers
        self.commands = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/stocks': self._handle_stocks,
            '/ask': self._handle_ask,
            '/deep': self._handle_deep,
            '/price': self._handle_price,
            '/news': self._handle_news,
            '/add': self._handle_add,
            '/remove': self._handle_remove,
            '/watchlist': self._handle_watchlist,
            '/interval': self._handle_interval,
            '/lang': self._handle_lang,
            '/now': self._handle_now,
        }
    
    def send_help_message(self):
        """Send help message to configured chat"""
        try:
            chat_id = int(self.config.telegram.chat_id)
            self._handle_help(chat_id, [], "System")
        except Exception as e:
            logger.error(f"Failed to send help message: {e}")

    def start_auto_news(self):
        """Start auto news scheduler"""
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._auto_news_loop, daemon=True)
        self.scheduler_thread.start()
        print(f"⏰ Auto news scheduler started (interval: {self.user_settings.get_interval()} min)")
        logger.info("Auto news scheduler started")

    def stop_auto_news(self):
        """Stop auto news scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Auto news scheduler stopped")

    def _auto_news_loop(self):
        """Auto news scheduler loop"""
        while self.scheduler_running:
            try:
                interval = self.user_settings.get_interval()
                watchlist = self.user_settings.get_watchlist()
                
                print(f"\n🔔 Checking news for: {', '.join(watchlist)}")
                
                sent_count = 0
                for symbol in watchlist:
                    if self.user_settings.should_send(symbol):
                        print(f"  📰 Sending news for {symbol}...")
                        self._send_auto_news(symbol)
                        self.user_settings.set_last_sent(symbol)
                        sent_count += 1
                    else:
                        last = self.user_settings.get_last_sent(symbol)
                        if last:
                            elapsed = (datetime.now() - last).total_seconds() / 60
                            print(f"  ⏳ {symbol}: waiting ({elapsed:.1f}/{interval} min)")
                
                if sent_count == 0:
                    print(f"  No news sent, next check in {interval} minutes")

                # Sleep for interval
                print(f"\n💤 Next check in {interval} minutes... (Ctrl+C to stop)")
                time.sleep(interval * 60)
                
            except Exception as e:
                logger.error(f"Error in auto news loop: {e}")
                print(f"❌ Error: {e}")
                time.sleep(60)

    def _send_auto_news(self, symbol: str):
        """Send auto news for a symbol"""
        try:
            chat_id = int(self.config.telegram.chat_id)
            news = self.fetcher.get_news(symbol, hours=24)
            
            if not news:
                print(f"  No news found for {symbol}")
                return
            
            # Get stock data
            stock_data = self.fetcher.get_stock_info(symbol)
            
            # Analyze
            print(f"  🤖 Analyzing news for {symbol}...")
            analysis = self.analyzer.analyze_news(
                stock_symbol=symbol,
                stock_name=symbol,
                stock_data=stock_data or {},
                news_items=news,
                keywords=[],
            )
            
            # Format and send
            from .telegram_notifier import TelegramNotifier
            notifier = TelegramNotifier(
                bot_token=self.bot_token,
                chat_id=str(chat_id),
            )
            
            message = notifier.format_news_alert(
                symbol=symbol,
                name=symbol,
                news_items=news,
                analysis=analysis,
                stock_data=stock_data,
            )
            
            if notifier.send_message(message):
                print(f"  ✅ Sent news for {symbol}")
                logger.info(f"Sent auto news for {symbol}")
            else:
                print(f"  ❌ Failed to send news for {symbol}")
            
        except Exception as e:
            logger.error(f"Error sending auto news for {symbol}: {e}")
            print(f"  ❌ Error: {e}")

        except Exception as e:
            logger.error(f"Error sending auto news for {symbol}: {e}")

    def register_alert(self, symbol: str, analysis: Dict[str, Any], news: list = None):
        """Register a recent alert for context in Q&A"""
        self.recent_alerts[symbol] = {
            'analysis': analysis,
            'timestamp': datetime.now().isoformat(),
        }
        if news:
            self.recent_news[symbol] = news

    def start_polling(self, interval: float = 2.0):
        """Start polling for messages"""
        logger.info("Starting interactive bot polling...")
        print("🤖 Interactive bot started! Send /help to see commands.")

        while True:
            try:
                updates = self._get_updates()
                for update in updates:
                    self._process_update(update)
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                time.sleep(5)

    def _get_updates(self, timeout: int = 10) -> list:
        """Get new messages from Telegram"""
        url = f"{self.base_url}/getUpdates"
        params = {
            'offset': self.last_update_id + 1,
            'timeout': timeout,
        }

        try:
            response = requests.get(url, params=params, timeout=timeout + 5)
            result = response.json()

            if result.get('ok'):
                updates = result.get('result', [])
                if updates:
                    self.last_update_id = updates[-1]['update_id']
                return updates
            return []
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []

    def _process_update(self, update: dict):
        """Process a single update/message"""
        message = update.get('message', {})
        message_id = message.get('message_id')
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '').strip()
        user = message.get('from', {}).get('first_name', 'User')

        if not text or not chat_id:
            return

        # Skip if already processed (avoid duplicates)
        msg_key = f"{chat_id}_{message_id}"
        if msg_key in self.processed_messages:
            return
        self.processed_messages.add(msg_key)

        # Keep only last 1000 processed messages
        if len(self.processed_messages) > 1000:
            self.processed_messages = set(list(self.processed_messages)[-500:])

        logger.info(f"Message from {user}: {text}")

        # Check if it's a command
        if text.startswith('/'):
            parts = text.split(maxsplit=2)
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            self._handle_command(chat_id, command, args, user)
        else:
            # Treat as a question
            self._handle_question(chat_id, text, user)

    def _handle_command(self, chat_id: int, command: str, args: list, user: str):
        """Handle bot commands"""
        handler = self.commands.get(command)
        if handler:
            handler(chat_id, args, user)
        else:
            self._send_message(chat_id, f"Unknown command: {command}\nSend /help for available commands.")

    def _handle_start(self, chat_id: int, args: list, user: str):
        """Handle /start command"""
        # Send full help message on start
        self._handle_help(chat_id, args, user)
    
    def _handle_help(self, chat_id: int, args: list, user: str):
        """Handle /help command - show detailed help with examples"""
        help_text = """🤖 *Stock Noti Bot - 使用指南*

━━━━━━━━━━━━━━━━━━━━
📊 *监控管理*
━━━━━━━━━━━━━━━━━━━━

`/watchlist` - 查看你的设置
`/add <股票>` - 添加监控
  示例: `/add TSLA`
  示例: `/add AAPL`

`/remove <股票>` - 移除监控
  示例: `/remove TSLA`

`/interval <分钟>` - 设置推送间隔
  示例: `/interval 5` → 每5分钟
  示例: `/interval 30` → 每30分钟
  示例: `/interval 60` → 每1小时

`/lang zh` - 切换中文
`/lang en` - 切换英文

`/now` - 立即获取新闻（不用等定时）
  示例: `/now`

━━━━━━━━━━━━━━━━━━━━
📈 *股票信息*
━━━━━━━━━━━━━━━━━━━━

`/stocks` - 查看监控的所有股票价格
`/price <股票>` - 查询实时价格
  示例: `/price NVDA`
  示例: `/price LUNR`

`/news <股票>` - 获取最新新闻
  示例: `/news NVDA`
  示例: `/news TSLA`

━━━━━━━━━━━━━━━━━━━━
🤖 *AI 智能分析*
━━━━━━━━━━━━━━━━━━━━

`/ask <股票> <问题>` - 问任何问题
  示例: `/ask NVDA 财报前应该买入吗？`
  示例: `/ask TSLA 现在的估值合理吗？`
  示例: `/ask LUNR NASA合同影响大吗？`

`/deep <股票> <主题>` - 深度分析
  可用主题: earnings, competition, risks, outlook
  示例: `/deep NVDA 竞争分析`
  示例: `/deep LUNR NASA合同`
  示例: `/deep TSLA 风险分析`

━━━━━━━━━━━━━━━━━━━━
💬 *直接提问*
━━━━━━━━━━━━━━━━━━━━

你也可以直接发消息，我会自动识别股票：
  示例: "NVDA的财报怎么样？"
  示例: "为什么LUNR涨了这么多？"
  示例: "TSLA值得长期持有吗？"

━━━━━━━━━━━━━━━━━━━━
⚙️ *当前设置*
"""

        # Add current settings
        watchlist = self.user_settings.get_watchlist()
        interval = self.user_settings.get_interval()
        lang = self.user_settings.get_language()
        
        help_text += f"""
📌 监控股票: {', '.join(watchlist) if watchlist else '未设置'}
⏱ 推送间隔: 每 {interval} 分钟
🌐 语言: {'中文' if lang == 'zh' else 'English'}

━━━━━━━━━━━━━━━━━━━━
⚡ 快速开始:
1. 用 /add 添加你想监控的股票
2. 用 /interval 设置推送间隔
3. 机器人会自动推送新闻分析！
"""
        
        self._send_message(chat_id, help_text)

    def _handle_stocks(self, chat_id: int, args: list, user: str):
        """Handle /stocks command"""
        # Use user's watchlist
        watchlist = self.user_settings.get_watchlist()

        if not watchlist:
            self._send_message(chat_id, "Your watchlist is empty. Use /add <symbol> to add stocks.")
            return

        message = "📊 *Your Watchlist*\n\n"

        for symbol in watchlist:
            # Find stock name from config
            name = symbol
            for stock in self.config.stocks:
                if stock.symbol == symbol:
                    name = stock.name
                    break

            # Get current price
            data = self.fetcher.get_stock_info(symbol)
            if data and data.get('price'):
                price = data['price']
                change_pct = data.get('change_percent', 0) or 0
                direction = "🔺" if change_pct >= 0 else "🔻"
                message += f"*{symbol}* - {name}\n"
                message += f"  ${price:.2f} {direction} {abs(change_pct):.2f}%\n\n"
            else:
                message += f"*{symbol}* - {name}\n\n"

        self._send_message(chat_id, message)

    def _handle_ask(self, chat_id: int, args: list, user: str):
        """Handle /ask command"""
        if len(args) < 2:
            self._send_message(chat_id, "Usage: /ask <symbol> <question>\nExample: /ask NVDA What's the outlook?")
            return

        symbol = args[0].upper()
        question = ' '.join(args[1:])

        self._answer_question(chat_id, symbol, question)

    def _handle_deep(self, chat_id: int, args: list, user: str):
        """Handle /deep command"""
        if len(args) < 2:
            topics = "earnings, competition, risks, outlook, catalysts"
            self._send_message(chat_id, f"Usage: /deep <symbol> <topic>\nTopics: {topics}\nExample: /deep NVDA competition")
            return

        symbol = args[0].upper()
        topic = ' '.join(args[1:])

        self._deep_dive(chat_id, symbol, topic)

    def _handle_price(self, chat_id: int, args: list, user: str):
        """Handle /price command"""
        if not args:
            self._send_message(chat_id, "Usage: /price <symbol>\nExample: /price NVDA")
            return

        symbol = args[0].upper()

        # Find stock name
        name = symbol
        for stock in self.config.stocks:
            if stock.symbol == symbol:
                name = stock.name
                break

        data = self.fetcher.get_stock_info(symbol)
        if data and data.get('price'):
            price = data['price']
            change = data.get('change', 0) or 0
            change_pct = data.get('change_percent', 0) or 0
            direction = "🔺" if change >= 0 else "🔻"

            message = f"""📊 *{symbol}* {name}

💰 Price: ${price:.2f}
{direction} Change: {abs(change):.2f} ({abs(change_pct):.2f}%)

📊 Volume: {data.get('volume', 'N/A'):,}
📈 Market Cap: {data.get('market_cap', 'N/A')}
📐 P/E: {data.get('pe_ratio', 'N/A')}

52W High: ${data.get('52_week_high', 'N/A')}
52W Low: ${data.get('52_week_low', 'N/A')}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
            self._send_message(chat_id, message)
        else:
            self._send_message(chat_id, f"Could not fetch price for {symbol}")

    def _handle_news(self, chat_id: int, args: list, user: str):
        """Handle /news command"""
        if not args:
            self._send_message(chat_id, "Usage: /news <symbol>\nExample: /news NVDA")
            return

        symbol = args[0].upper()

        # Find stock name
        name = symbol
        for stock in self.config.stocks:
            if stock.symbol == symbol:
                name = stock.name
                break

        news = self.fetcher.get_news(symbol, hours=48)

        if not news:
            self._send_message(chat_id, f"No recent news for {symbol}")
            return

        message = f"📰 *{symbol}* {name}\n\n*Recent News:*\n\n"

        for i, item in enumerate(news[:5], 1):
            title = item.get('title', 'No title')[:70]
            publisher = item.get('publisher', 'Unknown')
            url = item.get('url', '')

            message += f"*{i}. {title}*\n"
            message += f"📍 {publisher}\n"
            if url:
                message += f"🔗 [Link]({url})\n"
            message += "\n"

        self._send_message(chat_id, message)

    def _handle_question(self, chat_id: int, text: str, user: str):
        """Handle free-form question"""
        # Try to detect stock symbol from context or question
        symbol = self._detect_symbol(text)

        if symbol:
            self._answer_question(chat_id, symbol, text)
        else:
            # Generic response
            self._send_message(chat_id, f"""I'd be happy to help! Try:

• /ask <symbol> <question> - Ask about a specific stock
• /stocks - See monitored stocks
• Or include a stock symbol in your question

Example: "What's the outlook for NVDA?" """)

    def _detect_symbol(self, text: str) -> Optional[str]:
        """Try to detect stock symbol from text"""
        text_upper = text.upper()

        # Check user's watchlist first
        watchlist = self.user_settings.get_watchlist()
        for symbol in watchlist:
            if symbol in text_upper:
                return symbol

        # Check config stocks
        for stock in self.config.stocks:
            symbol = stock.symbol
            if symbol in text_upper:
                return symbol
            # Check keywords
            for keyword in (stock.keywords or []):
                if keyword.upper() in text_upper:
                    return symbol

        # Check recent alerts
        for symbol in self.recent_alerts.keys():
            if symbol in text_upper:
                return symbol

        return None

    def _answer_question(self, chat_id: int, symbol: str, question: str):
        """Answer a question about a stock"""
        self._send_message(chat_id, f"🤔 Thinking about {symbol}...")

        # Get context
        context = self.recent_alerts.get(symbol, {}).get('analysis')
        news = self.recent_news.get(symbol)

        # Get stock data
        stock_data = self.fetcher.get_stock_info(symbol)

        # Find name
        name = symbol
        for stock in self.config.stocks:
            if stock.symbol == symbol:
                name = stock.name
                break

        # Get answer
        result = self.analyzer.ask_question(
            symbol=symbol,
            name=name,
            question=question,
            context=context,
            news_items=news,
        )

        # Format response
        answer = result.get('answer', 'Sorry, I could not generate an answer.')
        detailed = result.get('detailed_explanation', '')
        takeaways = result.get('key_takeaways', [])
        risks = result.get('related_risks', [])
        follow_up = result.get('suggested_follow_up', '')

        message = f"📊 *{symbol}*\n\n💡 {answer}"

        if detailed:
            message += f"\n\n📝 {detailed}"

        if takeaways:
            message += "\n\n*Key Points:*"
            for t in takeaways[:3]:
                message += f"\n• {t}"

        if risks:
            message += "\n\n⚠️ *Risks:*"
            for r in risks[:2]:
                message += f"\n• {r}"

        if follow_up:
            message += f"\n\n❓ You might also ask: {follow_up}"

        self._send_message(chat_id, message)

    def _deep_dive(self, chat_id: int, symbol: str, topic: str):
        """Provide deep dive on a topic"""
        self._send_message(chat_id, f"🔍 Analyzing {topic} for {symbol}...")

        # Get stock data
        stock_data = self.fetcher.get_stock_info(symbol)
        news = self.recent_news.get(symbol) or self.fetcher.get_news(symbol, hours=48)

        # Find name
        name = symbol
        for stock in self.config.stocks:
            if stock.symbol == symbol:
                name = stock.name
                break

        result = self.analyzer.deep_dive(
            symbol=symbol,
            name=name,
            topic=topic,
            stock_data=stock_data,
            news_items=news,
        )

        if 'error' in result:
            self._send_message(chat_id, f"Error: {result['error']}")
            return

        # Format response
        overview = result.get('overview', '')
        bull_case = result.get('bull_case', '')
        bear_case = result.get('bear_case', '')
        key_points = result.get('key_points', [])
        catalysts = result.get('catalysts', [])
        action = result.get('investor_action', '')

        message = f"🔍 *Deep Dive: {topic}*\n📊 *{symbol}*\n\n"
        message += f"📖 *Overview*\n{overview}\n\n"

        if key_points:
            message += "*Key Points:*\n"
            for kp in key_points[:4]:
                point = kp.get('point', kp) if isinstance(kp, dict) else kp
                message += f"• {point}\n"
            message += "\n"

        if bull_case:
            message += f"🐂 *Bull Case*\n{bull_case}\n\n"

        if bear_case:
            message += f"🐻 *Bear Case*\n{bear_case}\n\n"

        if catalysts:
            message += "*Catalysts to Watch:*\n"
            for c in catalysts[:3]:
                message += f"• {c}\n"
            message += "\n"

        if action:
            message += f"⚡ *Action:* {action}"

        self._send_message(chat_id, message)

    def _handle_add(self, chat_id: int, args: list, user: str):
        """Handle /add command - add stock to watchlist"""
        if not args:
            self._send_message(chat_id, "Usage: /add <symbol>\nExample: /add AAPL")
            return

        symbol = args[0].upper()
        if self.user_settings.add_to_watchlist(symbol):
            self._send_message(chat_id, f"✅ Added {symbol} to watchlist!\n\nCurrent: {', '.join(self.user_settings.get_watchlist())}")
        else:
            self._send_message(chat_id, f"{symbol} is already in your watchlist.")

    def _handle_remove(self, chat_id: int, args: list, user: str):
        """Handle /remove command - remove stock from watchlist"""
        if not args:
            self._send_message(chat_id, "Usage: /remove <symbol>\nExample: /remove AAPL")
            return

        symbol = args[0].upper()
        if self.user_settings.remove_from_watchlist(symbol):
            self._send_message(chat_id, f"✅ Removed {symbol} from watchlist.\n\nCurrent: {', '.join(self.user_settings.get_watchlist())}")
        else:
            self._send_message(chat_id, f"{symbol} is not in your watchlist.")

    def _handle_watchlist(self, chat_id: int, args: list, user: str):
        """Handle /watchlist command - show current watchlist"""
        watchlist = self.user_settings.get_watchlist()
        interval = self.user_settings.get_interval()
        lang = self.user_settings.get_language()

        message = f"📊 *Your Watchlist*\n\n"
        message += f"📌 *Stocks:* {', '.join(watchlist) if watchlist else 'None'}\n"
        message += f"⏱ *Interval:* Every {interval} minutes\n"
        message += f"🌐 *Language:* {'中文' if lang == 'zh' else 'English'}\n\n"

        message += "*Commands:*\n"
        message += "• /add <symbol> - Add stock\n"
        message += "• /remove <symbol> - Remove stock\n"
        message += "• /interval <minutes> - Set interval\n"
        message += "• /lang zh/en - Set language"

        self._send_message(chat_id, message)

    def _handle_interval(self, chat_id: int, args: list, user: str):
        """Handle /interval command - set notification interval"""
        if not args:
            current = self.user_settings.get_interval()
            self._send_message(chat_id, f"Current interval: {current} minutes\n\nUsage: /interval <minutes>\nExample: /interval 30\n\nMin: 5, Max: 1440 (24 hours)")
            return

        try:
            minutes = int(args[0])
            if minutes < 5 or minutes > 1440:
                self._send_message(chat_id, "Interval must be between 5 and 1440 minutes (24 hours).")
                return

            new_interval = self.user_settings.set_interval(minutes)
            self._send_message(chat_id, f"✅ Interval set to {new_interval} minutes.")
        except ValueError:
            self._send_message(chat_id, "Please enter a valid number.\nExample: /interval 30")

    def _handle_lang(self, chat_id: int, args: list, user: str):
        """Handle /lang command - set language"""
        if not args:
            current = self.user_settings.get_language()
            self._send_message(chat_id, f"Current language: {'中文' if current == 'zh' else 'English'}\n\nUsage: /lang zh\n or /lang en")
            return

        lang = args[0].lower()
        if lang in ['zh', 'cn', 'chinese', '中文']:
            new_lang = self.user_settings.set_language('zh')
            self._send_message(chat_id, "✅ 语言已设置为中文。")
        elif lang in ['en', 'english']:
            new_lang = self.user_settings.set_language('en')
            self._send_message(chat_id, "✅ Language set to English.")
        else:
            self._send_message(chat_id, "Please use 'zh' for Chinese or 'en' for English.")

    def _handle_now(self, chat_id: int, args: list, user: str):
        """Handle /now command - send news immediately"""
        watchlist = self.user_settings.get_watchlist()
        
        if not watchlist:
            self._send_message(chat_id, "Your watchlist is empty. Use /add <symbol> first.")
            return
        
        self._send_message(chat_id, f"🔄 Fetching news for: {', '.join(watchlist)}...")
        
        for symbol in watchlist:
            self._send_auto_news(symbol)
            self.user_settings.set_last_sent(symbol)
        
        self._send_message(chat_id, f"✅ Done! Next auto update in {self.user_settings.get_interval()} minutes.")

    def _send_message(self, chat_id: int, text: str) -> bool:
        """Send a message to Telegram"""
        url = f"{self.base_url}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            return result.get('ok', False)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
