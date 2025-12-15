import os
import requests
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class NewsProcessor:
    """
    Processes news data for market analysis.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2"
    
    def fetch_and_process(self, symbol: str, ohlcv_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Fetch and process news for a symbol.
        """
        if not self.api_key:
            return []
        
        try:
            # Get date range from OHLCV data
            if ohlcv_df.empty:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
            else:
                end_date = ohlcv_df.index[-1].to_pydatetime() if hasattr(ohlcv_df.index[-1], 'to_pydatetime') else ohlcv_df.index[-1]
                start_date = end_date - timedelta(days=7)
            
            # Search for news
            query = f'"{symbol}" OR {symbol}'
            url = f"{self.base_url}/everything"
            params = {
                'q': query,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'sortBy': 'relevancy',
                'apiKey': self.api_key,
                'pageSize': 10
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                processed_news = []
                for article in articles[:5]:  # Limit to 5 most relevant
                    processed_news.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', ''),
                        'sentiment': self._analyze_sentiment(article.get('title', '') + ' ' + article.get('description', ''))
                    })
                
                return processed_news
            else:
                print(f"News API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        Simple sentiment analysis (placeholder - could use a proper NLP library).
        """
        positive_words = ['rise', 'up', 'gain', 'bullish', 'positive', 'strong', 'growth', 'profit']
        negative_words = ['fall', 'down', 'loss', 'bearish', 'negative', 'weak', 'decline', 'drop']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'</content>
<parameter name="filePath">mcp/trading/fetchers/news.py