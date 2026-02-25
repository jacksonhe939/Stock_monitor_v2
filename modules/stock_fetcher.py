"""
Stock data fetcher using Yahoo Finance
"""
import yfinance as yf
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class StockFetcher:
    """Fetch stock data and news from Yahoo Finance"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_time: Dict[str, datetime] = {}
        self.cache_ttl = timedelta(minutes=5)
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid"""
        if symbol not in self.cache_time:
            return False
        return datetime.now() - self.cache_time[symbol] < self.cache_ttl
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock information including price, volume, etc."""
        if self._is_cache_valid(symbol):
            return self.cache[symbol]
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Fast info for basic data
            fast_info = ticker.fast_info if hasattr(ticker, 'fast_info') else {}
            
            data = {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', symbol)),
                'price': fast_info.get('last_price') or info.get('currentPrice') or info.get('regularMarketPrice'),
                'previous_close': fast_info.get('previous_close') or info.get('previousClose'),
                'open': info.get('open') or info.get('regularMarketOpen'),
                'day_high': info.get('dayHigh'),
                'day_low': info.get('dayLow'),
                'volume': info.get('volume') or info.get('regularMarketVolume'),
                'avg_volume': info.get('averageVolume'),
                'market_cap': fast_info.get('market_cap') or info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'eps': info.get('trailingEps'),
                'dividend_yield': info.get('dividendYield'),
                '52_week_high': fast_info.get('fifty_two_week_high') or info.get('fiftyTwoWeekHigh'),
                '52_week_low': fast_info.get('fifty_two_week_low') or info.get('fiftyTwoWeekLow'),
                'beta': info.get('beta'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'timestamp': datetime.now().isoformat(),
            }
            
            # Calculate change
            if data['price'] and data['previous_close']:
                data['change'] = data['price'] - data['previous_close']
                data['change_percent'] = (data['change'] / data['previous_close']) * 100
            else:
                data['change'] = None
                data['change_percent'] = None
            
            self.cache[symbol] = data
            self.cache_time[symbol] = datetime.now()
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {e}")
            return None
    
    def get_news(self, symbol: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent news for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                logger.info(f"No news returned from Yahoo Finance for {symbol}")
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            logger.info(f"Looking for news after: {cutoff_time}")
            
            filtered_news = []
            for item in news[:20]:  # Limit to 20 items
                try:
                    content = item.get('content', {})
                    
                    # Parse timestamp - handle both int and ISO string formats
                    pub_date_raw = content.get('pubDate', 0)
                    if isinstance(pub_date_raw, (int, float)):
                        pub_time = datetime.fromtimestamp(pub_date_raw)
                    elif isinstance(pub_date_raw, str):
                        # ISO format string - remove timezone for comparison
                        pub_time_str = pub_date_raw.replace('Z', '').replace('+00:00', '')
                        try:
                            pub_time = datetime.fromisoformat(pub_time_str)
                        except:
                            pub_time = datetime.now()  # Default to now if parse fails
                    else:
                        continue  # Skip if can't parse
                    
                    # Make both naive (no timezone) for comparison
                    if hasattr(pub_time, 'tzinfo') and pub_time.tzinfo:
                        pub_time = pub_time.replace(tzinfo=None)
                    
                    title = content.get('title', 'No title')
                    
                    # Log for debugging
                    logger.debug(f"News: {title[:50]}... | {pub_time} vs {cutoff_time}")
                    
                    # Always include recent news (ignore time filter for now to test)
                    filtered_news.append({
                        'title': title,
                        'summary': content.get('summary', ''),
                        'url': content.get('canonicalUrl', {}).get('url', '') if isinstance(content.get('canonicalUrl'), dict) else '',
                        'publisher': content.get('provider', {}).get('displayName', '') if isinstance(content.get('provider'), dict) else '',
                        'published': pub_time.isoformat() if pub_time else '',
                        'thumbnail': '',
                        'tickers': [],
                    })
                except Exception as e:
                    logger.debug(f"Error parsing news item: {e}")
                    continue
            
            logger.info(f"Found {len(filtered_news)} news items for {symbol}")
            return filtered_news
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []
    
    def get_earnings_dates(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get upcoming earnings dates"""
        try:
            ticker = yf.Ticker(symbol)
            calendar = ticker.calendar
            
            if calendar is None or calendar.empty:
                return None
            
            return {
                'earnings_date': calendar.get('Earnings Date', [None])[0] if len(calendar) > 0 else None,
                'earnings_estimate': calendar.get('Earnings Average', [None])[0] if 'Earnings Average' in calendar.index else None,
                'revenue_estimate': calendar.get('Revenue Average', [None])[0] if 'Revenue Average' in calendar.index else None,
            }
            
        except Exception as e:
            logger.error(f"Error fetching earnings for {symbol}: {e}")
            return None
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get info for multiple stocks efficiently"""
        results = {}
        for symbol in symbols:
            info = self.get_stock_info(symbol)
            if info:
                results[symbol] = info
        return results
    
    def check_price_alert(self, symbol: str, threshold: float) -> Optional[Dict[str, Any]]:
        """Check if price change exceeds threshold"""
        info = self.get_stock_info(symbol)
        if not info or info.get('change_percent') is None:
            return None
        
        change_pct = abs(info['change_percent'])
        if change_pct >= threshold:
            return {
                'symbol': symbol,
                'price': info['price'],
                'change': info['change'],
                'change_percent': info['change_percent'],
                'direction': 'up' if info['change'] > 0 else 'down',
                'threshold': threshold,
            }
        return None
