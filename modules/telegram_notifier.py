"""
Telegram notification sender
"""
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send formatted stock alerts to Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a text message to Telegram"""
        url = f"{self.base_url}/sendMessage"
        
        # Truncate if too long (Telegram limit is 4096 chars)
        if len(text) > 4000:
            text = text[:4000] + "\n\n... (truncated)"
        
        # Escape problematic markdown characters
        # But keep basic formatting: *bold*, _italic_, [link](url)
        
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 400:
                # Try without markdown if parsing failed
                logger.warning("Markdown parsing failed, retrying without formatting")
                payload["parse_mode"] = None
                response = requests.post(url, json=payload, timeout=10)
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"Message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def _escape_markdown(self, text: str) -> str:
        """Escape special markdown characters"""
        # Characters that need escaping in Markdown
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    def format_news_alert(
        self,
        symbol: str,
        name: str,
        news_items: List[Dict[str, Any]],
        analysis: Dict[str, Any] = None,
        stock_data: Dict[str, Any] = None,
    ) -> str:
        """Format a news-focused alert with clickable links"""
        
        # Header
        sentiment = analysis.get('sentiment', 'neutral') if analysis else 'neutral'
        emoji = self._get_sentiment_emoji(sentiment)
        score = analysis.get('importance_score', 0) if analysis else 5
        score_emoji = self._get_score_emoji(score)
        
        message = f"📰 *{symbol}* - {name}\n"
        message += f"Score: {score_emoji} {score}/10 | Sentiment: {emoji} {sentiment.upper()}\n"
        message += "─" * 20 + "\n"
        
        # Price info if available
        if stock_data and stock_data.get('price'):
            price = stock_data['price']
            change_pct = stock_data.get('change_percent', 0) or 0
            direction = "🔺" if change_pct >= 0 else "🔻"
            message += f"\n💰 Price: ${price:.2f} {direction} {abs(change_pct):.2f}%\n"
        
        # News summary - show full summary
        if analysis:
            summary = analysis.get('summary') or analysis.get('news_summary', '')
            if summary:
                # Clean summary for markdown but don't truncate
                summary = summary.replace('*', '').replace('_', '').replace('[', '').replace(']', '')
                message += f"\n📋 Summary:\n{summary}\n"
        
        # Key analysis points
        if analysis:
            key_points = analysis.get('key_points', [])
            if key_points:
                message += "\n📊 Key Points:\n"
                for point in key_points[:4]:
                    point_text = str(point).replace('*', '').replace('_', '').replace('[', '').replace(']', '')[:150]
                    message += f"• {point_text}\n"
        
        # News items with clickable links
        if news_items:
            message += "\n📰 News:\n"
            for i, item in enumerate(news_items[:5], 1):
                title = item.get('title', 'No title')[:70]
                # Escape markdown in title
                title = title.replace('*', '').replace('_', '').replace('[', '').replace(']', '')
                publisher = item.get('publisher', '')
                url = item.get('url', '')
                published = item.get('published', '')
                
                message += f"\n*{i}. {title}*\n"
                if publisher:
                    message += f"📍 {publisher}"
                if published:
                    # Format time
                    try:
                        from datetime import datetime
                        if 'T' in published:
                            dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                            time_str = dt.strftime('%m/%d %H:%M')
                            message += f" | {time_str}"
                    except:
                        pass
                if url:
                    message += f"\n🔗 [View Article]({url})"
                message += "\n"
        
        # Key points
        if analysis:
            key_points = analysis.get('key_points', [])
            if key_points:
                message += "\n📊 Key Points:\n"
                for point in key_points[:3]:
                    # Clean up the point text
                    point_text = str(point).replace('*', '').replace('_', '')[:100]
                    message += f"• {point_text}\n"
            
            # Recommendation
            rec = analysis.get('recommendation', {})
            if rec:
                action = rec.get('action', '') if isinstance(rec, dict) else str(rec)
                if action:
                    message += f"\n⚡ Action: *{action.upper()}*"
        
        # Timestamp
        message += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        return message
        
        # News items with full details
        message += "\n*📰 最新新闻详情*\n"
        
        for i, item in enumerate(news_items[:5], 1):
            title = item.get('title', 'No title')
            url = item.get('url', '')
            publisher = item.get('publisher', 'Unknown')
            published = item.get('published', '')
            summary = item.get('summary', '')
            
            # Format time
            time_str = ""
            if published:
                try:
                    if 'T' in published:
                        dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m/%d %H:%M')
                except:
                    time_str = published[:10]
            
            message += f"\n*{i}. {title}*\n"
            message += f"📍 {publisher}"
            if time_str:
                message += f" | {time_str}"
            
            # Add summary if available
            if summary:
                message += f"\n📝 {summary[:150]}{'...' if len(summary) > 150 else ''}"
            
            if url:
                message += f"\n🔗 [查看原文]({url})"
            message += "\n"
        
        # Detailed Analysis
        if analysis:
            message += f"\n{'─' * 25}\n"
            message += "*🧠 AI 深度分析*\n\n"
            
            # What happened
            if analysis.get('detailed_analysis', {}).get('what_happened'):
                message += f"📌 *事件*: {analysis['detailed_analysis']['what_happened']}\n\n"
            
            # Why it matters
            if analysis.get('detailed_analysis', {}).get('why_it_matters'):
                message += f"💡 *重要性*: {analysis['detailed_analysis']['why_it_matters']}\n\n"
            
            # Key points with details
            key_points = analysis.get('key_points', [])
            if key_points:
                message += "*📊 关键点:*\n"
                for point in key_points[:4]:
                    message += f"• {point}\n"
                message += "\n"
            
            # Price impact
            price_impact = analysis.get('price_impact', {})
            if price_impact:
                impact_dir = price_impact.get('direction', 'neutral')
                impact_emoji = {'positive': '🟢', 'negative': '🔴', 'volatile': '⚡'}.get(impact_dir, '🟡')
                message += f"*股价影响*: {impact_emoji} {impact_dir.upper()}"
                if price_impact.get('magnitude'):
                    message += f" ({price_impact['magnitude']} impact)"
                if price_impact.get('reasoning'):
                    message += f"\n{price_impact['reasoning']}"
                message += "\n\n"
            
            # Risks and opportunities
            detailed = analysis.get('detailed_analysis', {})
            risks = detailed.get('risks', [])
            opps = detailed.get('opportunities', [])
            
            if risks:
                message += "⚠️ *风险:*\n"
                for r in risks[:2]:
                    message += f"• {r}\n"
                message += "\n"
            
            if opps:
                message += "🎯 *机会:*\n"
                for o in opps[:2]:
                    message += f"• {o}\n"
                message += "\n"
            
            # Recommendation
            rec = analysis.get('recommendation', {})
            if rec:
                action = rec.get('action', 'watch') if isinstance(rec, dict) else str(rec)
                confidence = rec.get('confidence', 'medium') if isinstance(rec, dict) else ''
                reasoning = rec.get('reasoning', '') if isinstance(rec, dict) else ''
                
                action_emoji = {'buy': '🟢', 'sell': '🔴', 'hold': '🟡', 'watch': '👀'}.get(action.lower(), '👉')
                message += f"⚡ *建议*: {action_emoji} **{action.upper()}**"
                if confidence:
                    message += f" (置信度: {confidence})"
                message += "\n"
                if reasoning:
                    message += f"_{reasoning}_\n"
                
                # Entry/Stop/Target
                if isinstance(rec, dict):
                    if rec.get('entry_point') and rec['entry_point'] != 'N/A':
                        message += f"📍 入场: {rec['entry_point']}\n"
                    if rec.get('stop_loss') and rec['stop_loss'] != 'N/A':
                        message += f"🛑 止损: {rec['stop_loss']}\n"
                    if rec.get('target') and rec['target'] != 'N/A':
                        message += f"🎯 目标: {rec['target']}\n"
            
            # Questions to consider
            questions = analysis.get('questions_to_consider', [])
            if questions:
                message += f"\n❓ *值得思考:*\n"
                for q in questions[:2]:
                    message += f"• {q}\n"
            
            # Catalysts to watch
            insights = analysis.get('analyst_insights', {})
            catalysts = insights.get('catalysts_to_watch', [])
            if catalysts:
                message += f"\n📅 *关注催化剂:*\n"
                for c in catalysts[:3]:
                    message += f"• {c}\n"
        
        # Timestamp
        message += f"\n{'─' * 25}\n"
        message += f"💬 有疑问? 回复此消息提问\n"
        message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}"
        
        return message
    
    def format_stock_alert(
        self,
        symbol: str,
        name: str,
        stock_data: Dict[str, Any],
        analysis: Dict[str, Any],
        news_items: List[Dict[str, Any]] = None,
    ) -> str:
        """Format a stock alert message - now includes more news details"""
        
        # Header
        emoji = self._get_sentiment_emoji(analysis.get('sentiment', 'neutral'))
        header = f"📊 *{symbol}* {name}"
        
        # Price section
        price = stock_data.get('price', 'N/A')
        change = stock_data.get('change')
        change_pct = stock_data.get('change_percent')
        
        if change is not None and change_pct is not None:
            direction = "🔺" if change >= 0 else "🔻"
            price_section = f"\n\n🔔 *价格提醒*\n${price:.2f} {direction} {abs(change_pct):.2f}%"
        else:
            price_section = f"\n\n🔔 *当前价格*\n${price}"
        
        # Importance score
        score = analysis.get('importance_score', 0)
        score_emoji = self._get_score_emoji(score)
        importance_section = f"\n\n📰 *新闻影响*: {score_emoji} {score}/10"
        
        # Sentiment
        sentiment = analysis.get('sentiment', 'neutral').upper()
        sentiment_section = f"\n*情绪*: {emoji} {sentiment}"
        
        # Key points
        key_points = analysis.get('key_points', [])
        points_section = ""
        if key_points:
            points_section = "\n\n📌 *Key Points*"
            for point in key_points[:3]:
                points_section += f"\n• {point}"
        
        # Summary
        summary = analysis.get('summary', '')
        summary_section = f"\n\n💡 *AI Analysis*\n{summary}" if summary else ""
        
        # Recommendation
        rec = analysis.get('recommendation', '')
        rec_section = f"\n\n⚡ *Action*: {rec}" if rec else ""
        
        # News section with full details
        news_section = ""
        if news_items:
            news_section = "\n\n📰 *最新新闻*"
            for i, item in enumerate(news_items[:3], 1):
                title = item.get('title', 'No title')[:60]
                url = item.get('url', '')
                publisher = item.get('publisher', '')
                time_str = ""
                if item.get('published'):
                    try:
                        dt = datetime.fromisoformat(item['published'].replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M')
                    except:
                        pass
                
                news_section += f"\n\n*{i}. {title}*"
                if publisher:
                    news_section += f"\n📍 {publisher}"
                if time_str:
                    news_section += f" | {time_str}"
                if url:
                    news_section += f"\n🔗 [链接]({url})"
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
        footer = f"\n\n⏰ {timestamp}"
        
        message = (
            header +
            price_section +
            importance_section +
            sentiment_section +
            points_section +
            summary_section +
            rec_section +
            links_section +
            footer
        )
        
        return message
    
    def format_price_alert(
        self,
        symbol: str,
        name: str,
        price: float,
        change: float,
        change_pct: float,
        threshold: float,
    ) -> str:
        """Format a price change alert"""
        direction = "🔺" if change >= 0 else "🔻"
        emoji = "🔥" if abs(change_pct) >= 5 else "⚠️"
        
        return f"""{emoji} *PRICE ALERT: {symbol}*

{name}

${price:.2f} {direction} {abs(change_pct):.2f}%

Threshold: {threshold}%

⏰ {datetime.now().strftime("%Y-%m-%d %H:%M %Z")}"""
    
    def format_earnings_reminder(
        self,
        symbol: str,
        name: str,
        earnings_date: str,
        eps_estimate: Optional[float] = None,
        revenue_estimate: Optional[float] = None,
    ) -> str:
        """Format an earnings reminder"""
        eps_str = f"${eps_estimate:.2f}" if eps_estimate else "N/A"
        rev_str = f"${revenue_estimate/1e9:.1f}B" if revenue_estimate else "N/A"
        
        return f"""📅 *EARNINGS REMINDER: {symbol}*

{name}

🗓 Earnings Date: {earnings_date}
📊 EPS Estimate: {eps_str}
💰 Revenue Estimate: {rev_str}

⏰ {datetime.now().strftime("%Y-%m-%d %H:%M %Z")}"""
    
    def send_stock_alert(
        self,
        symbol: str,
        name: str,
        stock_data: Dict[str, Any],
        analysis: Dict[str, Any],
        news_items: List[Dict[str, Any]] = None,
    ) -> bool:
        """Send a formatted stock alert"""
        message = self.format_stock_alert(symbol, name, stock_data, analysis, news_items)
        return self.send_message(message)
    
    def test_connection(self) -> bool:
        """Test Telegram connection"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=5)
            result = response.json()
            if result.get("ok"):
                bot_name = result.get("result", {}).get("first_name", "Unknown")
                logger.info(f"Connected to bot: {bot_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def _get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji for sentiment"""
        return {
            'bullish': '🟢',
            'bearish': '🔴',
            'neutral': '🟡',
        }.get(sentiment.lower(), '⚪')
    
    def _get_score_emoji(self, score: int) -> str:
        """Get emoji for importance score"""
        if score >= 8:
            return '🔥'
        elif score >= 6:
            return '⚡'
        elif score >= 4:
            return '📊'
        else:
            return '💤'
