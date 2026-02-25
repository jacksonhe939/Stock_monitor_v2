"""
User settings manager for Stock_Noti_beta
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserSettings:
    """Manage user-specific settings"""
    
    def __init__(self, settings_file: str = None):
        if settings_file is None:
            settings_file = Path(__file__).parent.parent / "user_settings.json"
        self.settings_file = Path(settings_file)
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
        return {
            'watchlist': ['NVDA', 'LUNR'],
            'interval_minutes': 60,
            'language': 'zh',
            'last_sent': {},
        }
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    # Watchlist
    def get_watchlist(self) -> List[str]:
        return self.settings.get('watchlist', ['NVDA', 'LUNR'])
    
    def add_to_watchlist(self, symbol: str) -> bool:
        symbol = symbol.upper()
        watchlist = self.get_watchlist()
        if symbol not in watchlist:
            watchlist.append(symbol)
            self.settings['watchlist'] = watchlist
            self._save_settings()
            return True
        return False
    
    def remove_from_watchlist(self, symbol: str) -> bool:
        symbol = symbol.upper()
        watchlist = self.get_watchlist()
        if symbol in watchlist:
            watchlist.remove(symbol)
            self.settings['watchlist'] = watchlist
            self._save_settings()
            return True
        return False
    
    def set_watchlist(self, symbols: List[str]) -> List[str]:
        self.settings['watchlist'] = [s.upper() for s in symbols]
        self._save_settings()
        return self.settings['watchlist']
    
    # Interval
    def get_interval(self) -> int:
        return self.settings.get('interval_minutes', 60)
    
    def set_interval(self, minutes: int) -> int:
        self.settings['interval_minutes'] = max(5, min(1440, minutes))  # 5 min to 24 hours
        self._save_settings()
        return self.settings['interval_minutes']
    
    # Language
    def get_language(self) -> str:
        return self.settings.get('language', 'zh')
    
    def set_language(self, lang: str) -> str:
        if lang.lower() in ['zh', 'cn', 'chinese', '中文']:
            self.settings['language'] = 'zh'
        else:
            self.settings['language'] = 'en'
        self._save_settings()
        return self.settings['language']
    
    # Last sent tracking
    def get_last_sent(self, symbol: str) -> Optional[datetime]:
        last = self.settings.get('last_sent', {}).get(symbol)
        if last:
            try:
                return datetime.fromisoformat(last)
            except:
                return None
        return None
    
    def set_last_sent(self, symbol: str, dt: datetime = None):
        if dt is None:
            dt = datetime.now()
        if 'last_sent' not in self.settings:
            self.settings['last_sent'] = {}
        self.settings['last_sent'][symbol] = dt.isoformat()
        self._save_settings()
    
    def should_send(self, symbol: str) -> bool:
        """Check if enough time has passed since last send"""
        last = self.get_last_sent(symbol)
        if last is None:
            return True
        elapsed = datetime.now() - last
        interval_seconds = self.get_interval() * 60
        return elapsed.total_seconds() >= interval_seconds
