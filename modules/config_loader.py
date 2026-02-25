"""
Configuration loader and validator
"""
import os
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class AIConfig(BaseModel):
    provider: str = "openai"
    api_key: str
    model: str = "gpt-4o-mini"
    base_url: Optional[str] = None

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        allowed = ['openai', 'anthropic', 'zhipu', 'deepseek', 'xai']
        if v not in allowed:
            raise ValueError(f"Provider must be one of: {allowed}")
        return v


class TelegramConfig(BaseModel):
    bot_token: str
    chat_id: str


class StockConfig(BaseModel):
    symbol: str
    name: str
    keywords: List[str] = Field(default_factory=list)

    @field_validator('keywords', mode='before')
    @classmethod
    def validate_keywords(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            # 如果是字符串，尝试解析为列表
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except:
                # 如果不是 JSON 格式，假设是逗号分隔
                return [kw.strip() for kw in v.split(',') if kw.strip()]
        return []
        if isinstance(v, list):
            return v
        return []


class AlertSettings(BaseModel):
    interval_minutes: int = 60
    min_importance: int = Field(default=5, ge=0, le=10)
    price_change_threshold: float = 3.0
    news_timeframe_hours: int = 24


class ScheduleConfig(BaseModel):
    enabled: bool = True
    cron: str = "0 9-16 * * 1-5"
    timezone: str = "America/New_York"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "logs/stock_noti.log"


class Config(BaseModel):
    ai: AIConfig
    telegram: TelegramConfig
    stocks: List[StockConfig]
    alert_settings: AlertSettings = AlertSettings()
    schedule: ScheduleConfig = ScheduleConfig()
    logging: LoggingConfig = LoggingConfig()


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file"""
    if config_path is None:
        # Try multiple locations
        candidates = [
            Path("config.yaml"),
            Path("Stock_Noti_beta/config.yaml"),
            Path(__file__).parent.parent / "config.yaml",
        ]
        for candidate in candidates:
            if candidate.exists():
                config_path = str(candidate)
                break
    
    if config_path is None or not Path(config_path).exists():
        raise FileNotFoundError(
            "config.yaml not found. Copy config.example.yaml to config.yaml and fill in your values."
        )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Support environment variable overrides
    if os.environ.get('AI_API_KEY'):
        data.setdefault('ai', {})['api_key'] = os.environ['AI_API_KEY']
    if os.environ.get('TELEGRAM_BOT_TOKEN'):
        data.setdefault('telegram', {})['bot_token'] = os.environ['TELEGRAM_BOT_TOKEN']
    if os.environ.get('TELEGRAM_CHAT_ID'):
        data.setdefault('telegram', {})['chat_id'] = os.environ['TELEGRAM_CHAT_ID']
    
    return Config(**data)


def create_example_config() -> str:
    """Return the example config content"""
    return """# Stock_Noti_beta Configuration
# Copy this file to config.yaml and fill in your values

ai:
  provider: "openai"
  api_key: "YOUR_API_KEY_HERE"
  model: "gpt-4o-mini"

telegram:
  bot_token: "YOUR_BOT_TOKEN_HERE"
  chat_id: "YOUR_CHAT_ID_HERE"

stocks:
  - symbol: "NVDA"
    name: "NVIDIA Corporation"
    keywords: ["NVIDIA", "AI chip", "GPU"]
  - symbol: "LUNR"
    name: "Intuitive Machines"
    keywords: ["Intuitive Machines", "NASA", "lunar"]
"""
