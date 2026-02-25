"""
Stock_Noti_beta - AI-powered stock news monitor
Main entry point
"""
import sys
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.config_loader import load_config, Config
from modules.stock_fetcher import StockFetcher
from modules.news_analyzer import NewsAnalyzer
from modules.telegram_notifier import TelegramNotifier
from modules.interactive_bot import InteractiveBot

# Setup logging
def setup_logging(config: Config):
    """Setup logging configuration"""
    log_dir = Path(config.logging.file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.logging.file),
            logging.StreamHandler(),
        ]
    )
    return logging.getLogger(__name__)


class StockMonitor:
    """Main stock monitoring class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.fetcher = StockFetcher()
        self.analyzer = NewsAnalyzer(
            provider=config.ai.provider,
            api_key=config.ai.api_key,
            model=config.ai.model,
            base_url=config.ai.base_url,
        )
        self.notifier = TelegramNotifier(
            bot_token=config.telegram.bot_token,
            chat_id=config.telegram.chat_id,
        )
        
        # Track last notification times
        self.last_notification: Dict[str, datetime] = {}
    
    def run_once(self) -> Dict[str, Any]:
        """Run a single monitoring cycle"""
        self.logger.info("Starting monitoring cycle...")
        results = {}
        
        for stock in self.config.stocks:
            symbol = stock.symbol  # Pydantic model, use attribute access
            self.logger.info(f"Processing {symbol}...")
            
            try:
                # Fetch stock data
                stock_data = self.fetcher.get_stock_info(symbol)
                if not stock_data:
                    self.logger.warning(f"Could not fetch data for {symbol}")
                    continue
                
                # Fetch news
                news = self.fetcher.get_news(
                    symbol,
                    hours=self.config.alert_settings.news_timeframe_hours
                )
                
                # Check if we should notify (rate limiting)
                should_notify = self._should_notify(symbol)
                
                # Analyze news
                analysis = self.analyzer.analyze_news(
                    stock_symbol=symbol,
                    stock_name=stock.name,
                    stock_data=stock_data,
                    news_items=news,
                    keywords=stock.keywords or [],
                )
                
                results[symbol] = {
                    'stock_data': stock_data,
                    'news': news,
                    'analysis': analysis,
                }
                
                # Send notification if score is high enough
                if (should_notify and 
                    analysis.get('importance_score', 0) >= self.config.alert_settings.min_importance):
                    self.notifier.send_stock_alert(
                        symbol=symbol,
                        name=stock.name,
                        stock_data=stock_data,
                        analysis=analysis,
                        news_items=news,
                    )
                    self.last_notification[symbol] = datetime.now()
                    self.logger.info(f"Sent notification for {symbol}")
                
                # Check price alerts
                price_alert = self.fetcher.check_price_alert(
                    symbol,
                    self.config.alert_settings.price_change_threshold
                )
                if price_alert:
                    self.notifier.send_message(
                        self.notifier.format_price_alert(
                            symbol=symbol,
                            name=stock.name,
                            price=price_alert['price'],
                            change=price_alert['change'],
                            change_pct=price_alert['change_percent'],
                            threshold=price_alert['threshold'],
                        )
                    )
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        self.logger.info("Monitoring cycle complete")
        return results
    
    def _should_notify(self, symbol: str) -> bool:
        """Check if enough time has passed since last notification"""
        if symbol not in self.last_notification:
            return True
        
        elapsed = datetime.now() - self.last_notification[symbol]
        min_interval = self.config.alert_settings.interval_minutes * 60  # Convert to seconds
        
        return elapsed.total_seconds() >= min_interval
    
    def test_telegram(self) -> bool:
        """Test Telegram connection"""
        return self.notifier.test_connection()
    
    def test_ai(self) -> bool:
        """Test AI connection"""
        try:
            response = self.analyzer._call_ai("Respond with: OK")
            return "OK" in response.upper()
        except Exception as e:
            self.logger.error(f"AI test failed: {e}")
            return False
    
    def send_news_alerts(self, min_importance: int = None) -> Dict[str, Any]:
        """Send news-focused alerts for all stocks"""
        self.logger.info("Sending news alerts...")
        results = {}
        
        threshold = min_importance or self.config.alert_settings.min_importance
        
        for stock in self.config.stocks:
            symbol = stock.symbol  # Pydantic model, use attribute access
            self.logger.info(f"Processing news for {symbol}...")
            
            try:
                # Fetch stock data
                stock_data = self.fetcher.get_stock_info(symbol)
                
                # Fetch news
                news = self.fetcher.get_news(
                    symbol,
                    hours=self.config.alert_settings.news_timeframe_hours
                )
                
                if not news:
                    self.logger.info(f"No news for {symbol}")
                    continue
                
                # Analyze news
                analysis = self.analyzer.analyze_news(
                    stock_symbol=symbol,
                    stock_name=stock.name,
                    stock_data=stock_data or {},
                    news_items=news,
                    keywords=stock.keywords or [],
                )
                
                score = analysis.get('importance_score', 0)
                
                results[symbol] = {
                    'news_count': len(news),
                    'importance_score': score,
                    'sentiment': analysis.get('sentiment'),
                    'sent': False,
                }
                
                # Send if score meets threshold
                if score >= threshold:
                    message = self.notifier.format_news_alert(
                        symbol=symbol,
                        name=stock.name,
                        news_items=news,
                        analysis=analysis,
                        stock_data=stock_data,
                    )
                    if self.notifier.send_message(message):
                        results[symbol]['sent'] = True
                        self.logger.info(f"Sent news alert for {symbol} (score: {score})")
                else:
                    self.logger.info(f"Skipped {symbol} (score {score} < {threshold})")
                    
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results
    
    def run_scheduled(self):
        """Run with scheduler"""
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BlockingScheduler(timezone=self.config.schedule.timezone)
        
        # Add job based on cron expression
        trigger = CronTrigger.from_crontab(self.config.schedule.cron)
        scheduler.add_job(self.run_once, trigger)
        
        self.logger.info(f"Scheduler started: {self.config.schedule.cron}")
        self.logger.info("Press Ctrl+C to exit")
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Scheduler stopped")


def main():
    parser = argparse.ArgumentParser(description="Stock_Noti_beta - AI-powered stock monitor")
    parser.add_argument('--config', '-c', help='Path to config file')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--test', action='store_true', help='Test connections')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode for testing')
    parser.add_argument('--news', action='store_true', help='Send news-focused alerts')
    parser.add_argument('--bot', action='store_true', help='Start interactive bot for Q&A')
    parser.add_argument('--send-help', action='store_true', help='Send /help on bot start')
    parser.add_argument('--symbol', '-s', help='Analyze single symbol')
    parser.add_argument('--min-score', type=int, default=5, help='Minimum importance score to send (0-10)')
    args = parser.parse_args()
    
    # Load config
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nRun: cp config.example.yaml config.yaml")
        print("Then edit config.yaml with your API keys")
        sys.exit(1)
    except Exception as e:
        print(f"Config error: {e}")
        sys.exit(1)
    
    # Setup logging
    logger = setup_logging(config)
    monitor = StockMonitor(config)
    
    # Test mode
    if args.test:
        if not args.quiet:
            print("Testing connections...")
        telegram_ok = monitor.test_telegram()
        ai_ok = monitor.test_ai()
        
        if not args.quiet:
            print(f"Telegram: {'✅' if telegram_ok else '❌'}")
            print(f"AI API: {'✅' if ai_ok else '❌'}")
        
        if telegram_ok and ai_ok and not args.quiet:
            monitor.notifier.send_message("✅ Stock_Noti_beta test successful!")
        
        sys.exit(0 if (telegram_ok and ai_ok) else 1)
    
    # Interactive bot mode
    if args.bot:
        print("🤖 Starting interactive bot...")
        bot = InteractiveBot(
            bot_token=config.telegram.bot_token,
            analyzer=monitor.analyzer,
            fetcher=monitor.fetcher,
            config=config,
        )
        
        # Send help on start if requested
        if args.send_help:
            bot.send_help_message()
        
        # Start scheduler for auto news推送
        bot.start_auto_news()
        
        bot.start_polling()
        sys.exit(0)
    
    # Single symbol mode
    if args.symbol:
        # Override stocks list
        config.stocks = [{
            'symbol': args.symbol.upper(),
            'name': args.symbol.upper(),
            'keywords': [],
        }]
    
    # Run mode
    if args.news:
        # News-only mode - send news alerts
        results = monitor.send_news_alerts(min_importance=args.min_score)
        print(f"\nNews alerts sent:")
        for symbol, data in results.items():
            status = "✅ Sent" if data.get('sent') else "⏭️ Skipped"
            print(f"  {symbol}: {status} (score: {data.get('importance_score', 'N/A')})")
    elif args.once or not config.schedule.enabled:
        monitor.run_once()
    else:
        monitor.run_scheduled()


if __name__ == "__main__":
    main()
