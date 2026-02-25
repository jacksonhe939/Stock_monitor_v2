"""
News analyzer using AI to evaluate stock impact
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """Analyze news impact on stock prices using AI"""
    
    PROVIDER_CONFIGS = {
        'openai': {
            'base_url': 'https://api.openai.com/v1',
            'default_model': 'gpt-4o-mini',
        },
        'anthropic': {
            'base_url': 'https://api.anthropic.com/v1',
            'default_model': 'claude-3-haiku-20240307',
        },
        'zhipu': {
            'base_url': 'https://open.bigmodel.cn/api/paas/v4',
            'default_model': 'glm-4-flash',
        },
        'deepseek': {
            'base_url': 'https://api.deepseek.com/v1',
            'default_model': 'deepseek-chat',
        },
        'xai': {
            'base_url': 'https://api.x.ai/v1',
            'default_model': 'grok-4-latest',
        },
    }
    
    def __init__(self, provider: str, api_key: str, model: Optional[str] = None, base_url: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        self.config = self.PROVIDER_CONFIGS.get(provider, {})
        self.model = model or self.config.get('default_model', 'gpt-4o-mini')
        self.base_url = base_url or self.config.get('base_url')
        self._client = None
    
    @property
    def client(self):
        """Lazy load the AI client"""
        if self._client is None:
            if self.provider == 'anthropic':
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            else:
                # OpenAI-compatible API (openai, deepseek, zhipu, xai)
                import openai
                self._client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
        return self._client
    
    def analyze_news(
        self,
        stock_symbol: str,
        stock_name: str,
        stock_data: Dict[str, Any],
        news_items: List[Dict[str, Any]],
        keywords: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze news impact on stock price
        
        Returns:
            {
                'importance_score': 0-10,
                'sentiment': 'bullish' | 'bearish' | 'neutral',
                'summary': str,
                'key_points': List[str],
                'price_impact': str,
                'recommendation': str,
            }
        """
        if not news_items:
            return {
                'importance_score': 0,
                'sentiment': 'neutral',
                'summary': 'No recent news found.',
                'key_points': [],
                'price_impact': 'neutral',
                'recommendation': 'No action needed',
            }
        
        # Build prompt
        prompt = self._build_prompt(stock_symbol, stock_name, stock_data, news_items, keywords)
        
        try:
            response = self._call_ai(prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Error analyzing news for {stock_symbol}: {e}")
            return {
                'importance_score': 0,
                'sentiment': 'neutral',
                'summary': f'Analysis failed: {str(e)}',
                'key_points': [],
                'price_impact': 'unknown',
                'recommendation': 'Manual review needed',
            }
    
    def _build_prompt(
        self,
        symbol: str,
        name: str,
        stock_data: Dict[str, Any],
        news_items: List[Dict[str, Any]],
        keywords: List[str] = None,
    ) -> str:
        """Build the analysis prompt with detailed news analysis"""
        
        # Format stock data
        stock_info = f"""
Stock: {name} ({symbol})
Current Price: ${stock_data.get('price', 'N/A')}
Change: {stock_data.get('change', 'N/A')} ({stock_data.get('change_percent', 'N/A')}%)
Volume: {stock_data.get('volume', 'N/A')}
Market Cap: {stock_data.get('market_cap', 'N/A')}
P/E Ratio: {stock_data.get('pe_ratio', 'N/A')}
52W High: ${stock_data.get('52_week_high', 'N/A')}
52W Low: ${stock_data.get('52_week_low', 'N/A')}
"""
        
        # Format news with full content
        news_text = ""
        for i, item in enumerate(news_items[:6], 1):
            news_text += f"\n{'='*50}\n"
            news_text += f"NEWS {i}:\n"
            news_text += f"Title: {item.get('title', 'No title')}\n"
            if item.get('summary'):
                news_text += f"Content: {item['summary'][:500]}\n"
            news_text += f"Source: {item.get('publisher', 'Unknown')}\n"
            news_text += f"Published: {item.get('published', 'Unknown')}\n"
        
        keywords_str = ", ".join(keywords) if keywords else "N/A"
        
        prompt = f"""You are an expert financial analyst with deep knowledge of stock markets, earnings analysis, and news impact assessment. Provide a comprehensive analysis of the following news for {symbol}.

{stock_info}

RECENT NEWS (last 24-48 hours):
{news_text}

RELEVANT KEYWORDS: {keywords_str}

Provide a detailed analysis in JSON format:
{{
  "importance_score": <0-10 integer>,
  "sentiment": "<bullish|bearish|neutral>",
  "market_context": "<1-2 sentences about overall market/sector context>",
  "news_summary": "<detailed 3-4 sentence summary of what happened and why it matters>",
  "detailed_analysis": {{
    "what_happened": "<clear explanation of the news event>",
    "why_it_matters": "<why this is significant for the stock>",
    "potential_outcomes": ["<outcome 1>", "<outcome 2>"],
    "risks": ["<risk 1>", "<risk 2>"],
    "opportunities": ["<opportunity 1>", "<opportunity 2>"]
  }},
  "price_impact": {{
    "direction": "<positive|negative|neutral|volatile>",
    "magnitude": "<high|medium|low>",
    "timeframe": "<immediate|days|weeks>",
    "reasoning": "<why this impact is expected>"
  }},
  "key_points": ["<point 1 with detail>", "<point 2 with detail>", "<point 3 with detail>", "<point 4>"],
  "analyst_insights": {{
    "consensus_view": "<what most analysts think>",
    "contrarian_view": "<alternative perspective if relevant>",
    "catalysts_to_watch": ["<upcoming event 1>", "<upcoming event 2>"]
  }},
  "recommendation": {{
    "action": "<buy|hold|sell|watch>",
    "confidence": "<high|medium|low>",
    "reasoning": "<detailed reasoning>",
    "entry_point": "<suggested entry price or N/A>",
    "stop_loss": "<suggested stop loss or N/A>",
    "target": "<price target or N/A>"
  }},
  "questions_to_consider": ["<question investor should ask 1>", "<question 2>"]
}}

Scoring guide:
- 9-10: Major event (M&A, blockbuster earnings, FDA approval, major lawsuit/settlement)
- 7-8: Important (analyst upgrade/downgrade with PT change, large contract win, guidance update, earnings preview)
- 5-6: Moderate (sector news affecting stock, peer news, minor announcements)
- 3-4: Low (routine news, general market commentary)
- 0-2: Not relevant

Be thorough but concise. Focus on actionable insights for an investor. Respond ONLY with valid JSON."""
        
        return prompt
    
    def _call_ai(self, prompt: str) -> str:
        """Call the AI API"""
        if self.provider == 'anthropic':
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        else:
            # OpenAI-compatible
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured data"""
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response.split("```json")[1].split("```")[0]
            elif response.startswith("```"):
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback parsing
            return {
                'importance_score': 5,
                'sentiment': 'neutral',
                'summary': response[:200],
                'key_points': [],
                'price_impact': 'neutral',
                'recommendation': 'Review manually',
            }
    
    def ask_question(
        self,
        symbol: str,
        name: str,
        question: str,
        context: Dict[str, Any] = None,
        news_items: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Answer user question about news or stock
        
        Args:
            symbol: Stock symbol
            name: Stock name
            question: User's question
            context: Previous analysis context
            news_items: Relevant news items
        
        Returns:
            Dict with answer and related info
        """
        # Build context
        context_str = ""
        if context:
            context_str = f"""
Previous Analysis:
- Importance: {context.get('importance_score', 'N/A')}/10
- Sentiment: {context.get('sentiment', 'N/A')}
- Summary: {context.get('news_summary', context.get('summary', 'N/A'))}
- Recommendation: {context.get('recommendation', {}).get('action', 'N/A') if isinstance(context.get('recommendation'), dict) else context.get('recommendation', 'N/A')}
"""
        
        news_context = ""
        if news_items:
            news_context = "\nRelevant News:\n"
            for i, item in enumerate(news_items[:3], 1):
                news_context += f"{i}. {item.get('title', '')}\n"
                if item.get('summary'):
                    news_context += f"   {item['summary'][:200]}...\n"
        
        prompt = f"""You are a helpful financial analyst assistant. A user is asking about {symbol} ({name}).

{context_str}
{news_context}

User Question: {question}

Provide a helpful, informative response in JSON format:
{{
  "answer": "<direct answer to the question, 2-4 sentences>",
  "detailed_explanation": "<more detailed explanation if needed>",
  "key_takeaways": ["<takeaway 1>", "<takeaway 2>"],
  "related_risks": ["<risk to consider 1>", "<risk 2>"],
  "suggested_follow_up": "<suggested question the user might want to ask next>",
  "confidence": "<high|medium|low>"
}}

Be helpful, accurate, and focus on what the user wants to know. If you don't have enough information, say so and suggest what additional info would help. Respond ONLY with valid JSON."""

        try:
            response = self._call_ai(prompt)
            result = self._parse_response(response)
            result['symbol'] = symbol
            result['question'] = question
            return result
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                'answer': f"Sorry, I couldn't process your question. Error: {str(e)}",
                'symbol': symbol,
                'question': question,
            }
    
    def deep_dive(
        self,
        symbol: str,
        name: str,
        topic: str,
        stock_data: Dict[str, Any] = None,
        news_items: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Provide deep dive analysis on a specific topic
        
        Args:
            symbol: Stock symbol
            name: Stock name
            topic: Topic to analyze (e.g., "earnings", "competition", "risks")
        
        Returns:
            Detailed analysis on the topic
        """
        stock_context = ""
        if stock_data:
            stock_context = f"""
Current Stock Data:
- Price: ${stock_data.get('price', 'N/A')}
- Change: {stock_data.get('change_percent', 'N/A')}%
- P/E: {stock_data.get('pe_ratio', 'N/A')}
- Market Cap: {stock_data.get('market_cap', 'N/A')}
"""
        
        news_context = ""
        if news_items:
            news_context = "\nRecent News for Context:\n"
            for item in news_items[:3]:
                news_context += f"- {item.get('title', '')}\n"

        prompt = f"""You are an expert financial analyst. Provide a deep dive analysis on {topic} for {symbol} ({name}).

{stock_context}
{news_context}

Topic: {topic}

Provide a comprehensive analysis in JSON format:
{{
  "topic": "{topic}",
  "overview": "<2-3 sentence overview of this topic for {symbol}>",
  "key_points": [
    {{"point": "<point 1>", "explanation": "<why this matters>"}},
    {{"point": "<point 2>", "explanation": "<why this matters>"}}
  ],
  "bull_case": "<positive scenario and potential upside>",
  "bear_case": "<negative scenario and potential downside>",
  "timeline": "<when might this play out>",
  "catalysts": ["<event that could impact this topic>"],
  "metrics_to_watch": ["<key metric 1>", "<key metric 2>"],
  "investor_action": "<what should investor do regarding this topic>",
  "confidence": "<high|medium|low>"
}}

Be thorough, balanced, and actionable. Respond ONLY with valid JSON."""

        try:
            response = self._call_ai(prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Error in deep dive: {e}")
            return {'error': str(e), 'topic': topic}

    def batch_analyze(
        self,
        stocks: List[Dict[str, Any]],
        news_data: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze multiple stocks"""
        results = {}
        for stock in stocks:
            symbol = stock['symbol']
            news = news_data.get(symbol, [])
            analysis = self.analyze_news(
                stock_symbol=symbol,
                stock_name=stock['name'],
                stock_data={},  # Caller should provide stock_data
                news_items=news,
                keywords=stock.get('keywords', []),
            )
            results[symbol] = analysis
        return results
